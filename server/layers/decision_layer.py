"""
Decision Layer - Orchestration and Agent Sequencing

This layer determines which agents to execute, in what order,
and manages conditional logic based on context and user preferences.
"""

import json
import time
from typing import Dict, Any, List, Optional
from .perception_layer import PerceptionLayer
from .memory_layer import MemoryLayer


class DecisionLayer:
    """
    Decision Layer handles orchestration, agent sequencing, and execution logic
    """
    
    # Available agents and their capabilities
    AVAILABLE_AGENTS = {
        'legal_extractor': {
            'name': 'Legal Extractor Agent',
            'description': 'Extracts structured legal information from documents',
            'input_required': ['document_text'],
            'output_provides': ['case_name', 'court', 'date', 'facts', 'legal_issues', 'holdings', 'reasoning', 'citations', 'disposition'],
            'dependencies': []
        },
        'brief_generator': {
            'name': 'Brief Generator Agent',
            'description': 'Generates comprehensive legal briefs from extracted data',
            'input_required': ['extracted_data'],
            'output_provides': ['issue', 'facts', 'holding', 'reasoning', 'key_citations', 'word_count', 'confidence_score'],
            'dependencies': ['legal_extractor']
        },
        'citation_normalizer': {
            'name': 'Citation Normalizer Agent',
            'description': 'Normalizes citations to standard formats (Bluebook, APA, MLA, Chicago)',
            'input_required': ['citations'],
            'output_provides': ['normalized_citations', 'format_used', 'total_processed'],
            'dependencies': ['legal_extractor']
        },
        'case_retriever': {
            'name': 'Case Retriever Agent',
            'description': 'Finds similar cases and legal precedents',
            'input_required': ['legal_issues', 'key_phrases'],
            'output_provides': ['similar_cases', 'precedents', 'statutes', 'relevance_scores'],
            'dependencies': ['legal_extractor']
        },
        'comparator': {
            'name': 'Comparator Agent',
            'description': 'Compares target case with similar cases and highlights similarities',
            'input_required': ['target_case', 'similar_cases'],
            'output_provides': ['similarity_analysis', 'conflicting_holdings', 'reasoning_comparison'],
            'dependencies': ['legal_extractor', 'case_retriever']
        }
    }
    
    def __init__(
        self,
        perception_layer: PerceptionLayer,
        memory_layer: MemoryLayer
    ):
        """
        Initialize Decision Layer
        
        Args:
            perception_layer: Perception layer instance for LLM interactions
            memory_layer: Memory layer instance for context and preferences
        """
        self.perception = perception_layer
        self.memory = memory_layer
    
    def decide_execution_plan(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        detail_level: str = 'summary'
    ) -> Dict[str, Any]:
        """
        Decide the optimal execution plan based on user request and context
        
        Args:
            user_request: User's request/input
            context: Current context/state
            detail_level: 'summary' or 'detailed' for logging verbosity
            
        Returns:
            Execution plan with agent sequence and logic
        """
        start_time = time.time()
        
        # Log based on detail level
        if detail_level == 'detailed':
            print(f"  🎯 [Decision Layer] Orchestration Planning - Starting")
            print(f"  [Decision] User request: {user_request[:100]}...")
        else:
            print(f"  🎯 [Decision Layer] Orchestration Planning - Starting")
        
        try:
            # Get user preferences
            preferences = self.memory.get_preferences()
            
            # Prepare context
            if not context:
                context = self.memory.get_session_context()
            
            # Add preferences to context
            context['preferences'] = preferences
            
            # Get orchestration prompt
            prompt = self._build_orchestration_prompt(user_request, context)
            
            # Get LLM preferences from memory
            llm_prefs = preferences.get('llm', {})
            preferred_model = llm_prefs.get('primary_model', 'gemini')
            temperature = llm_prefs.get('temperature', 0.1)
            
            # Use Perception Layer to get orchestration decision
            result = self.perception.process_with_llm(
                prompt=prompt,
                context=context,
                preferred_model=preferred_model,
                temperature=temperature,  # Low temperature for consistent orchestration
                detail_level=detail_level
            )
            
            if not result['success']:
                # Fall back to rule-based orchestration
                return self._get_rule_based_plan(user_request, context, time.time() - start_time)
            
            # Parse the orchestration plan from LLM response
            plan = self.perception.parse_json_response(result['response'])
            
            if not plan:
                # Fall back to rule-based orchestration
                return self._get_rule_based_plan(user_request, context, time.time() - start_time)
            
            # Validate the plan
            validation = self.validate_execution_plan(plan)
            
            print(f"  ✅ [Decision Layer] Orchestration Planning - Completed")
            
            return {
                'success': True,
                'plan': plan,
                'validation': validation,
                'model_used': result.get('model_used', 'unknown'),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Decision-making failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _build_orchestration_prompt(
        self,
        user_request: str,
        context: Dict[str, Any]
    ) -> str:
        """Build the orchestration prompt"""
        # Format available agents
        agents_info = "\n".join([
            f"- {agent_id}: {info['description']} (requires: {', '.join(info['input_required'])})"
            for agent_id, info in self.AVAILABLE_AGENTS.items()
        ])
        
        # Get prompt from perception layer
        prompt = self.perception.get_prompt(
            'orchestration',
            available_agents=agents_info,
            user_request=user_request,
            current_context=json.dumps(context, indent=2),
            preferences=json.dumps(context.get('preferences', {}), indent=2)
        )
        
        return prompt
    
    def _get_rule_based_plan(
        self,
        user_request: str,
        context: Dict[str, Any],
        processing_time: float
    ) -> Dict[str, Any]:
        """
        Generate a rule-based execution plan when LLM is unavailable
        
        Args:
            user_request: User's request
            context: Current context
            processing_time: Time spent so far
            
        Returns:
            Rule-based execution plan
        """
        try:
            request_lower = user_request.lower()
            preferences = context.get('preferences', {})
            
            # Determine sequence based on request patterns and preferences
            if 'brief' in request_lower or 'summary' in request_lower:
                sequence = ['legal_extractor', 'brief_generator', 'citation_normalizer']
            elif 'extract' in request_lower or 'analyze' in request_lower:
                sequence = ['legal_extractor', 'citation_normalizer']
            elif 'citation' in request_lower:
                sequence = ['legal_extractor', 'citation_normalizer']
            elif 'similar' in request_lower or 'precedent' in request_lower:
                sequence = ['legal_extractor', 'case_retriever', 'comparator']
            else:
                # Default based on auto_generate_brief preference
                if preferences.get('general', {}).get('auto_generate_brief', False):
                    sequence = ['legal_extractor', 'brief_generator', 'citation_normalizer']
                else:
                    sequence = ['legal_extractor', 'citation_normalizer']
            
            plan = {
                'analysis': f"Rule-based orchestration for: {user_request[:100]}...",
                'selected_agents': [
                    {
                        'agent_id': agent,
                        'reason': f'Required for {agent} based on request pattern',
                        'priority': i + 1,
                        'required_inputs': self.AVAILABLE_AGENTS[agent]['input_required'],
                        'expected_outputs': self.AVAILABLE_AGENTS[agent]['output_provides']
                    }
                    for i, agent in enumerate(sequence)
                ],
                'execution_sequence': sequence,
                'conditional_logic': {
                    'if_extraction_fails': 'skip_all_subsequent',
                    'if_no_citations': 'skip_citation_normalization'
                },
                'confidence': 0.7
            }
            
            validation = self.validate_execution_plan(plan)
            
            return {
                'success': True,
                'plan': plan,
                'validation': validation,
                'model_used': 'rule-based',
                'processing_time': processing_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Rule-based planning failed: {str(e)}',
                'processing_time': processing_time
            }
    
    def validate_execution_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an execution plan
        
        Args:
            plan: Execution plan to validate
            
        Returns:
            Validation result with warnings and errors
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check required fields
        required_fields = ['selected_agents', 'execution_sequence']
        for field in required_fields:
            if field not in plan:
                validation['is_valid'] = False
                validation['errors'].append(f"Missing required field: {field}")
        
        if 'execution_sequence' not in plan:
            return validation
        
        sequence = plan['execution_sequence']
        
        # Check agent dependencies
        for i, agent in enumerate(sequence):
            if agent in self.AVAILABLE_AGENTS:
                dependencies = self.AVAILABLE_AGENTS[agent]['dependencies']
                for dep in dependencies:
                    if dep not in sequence[:i]:
                        validation['warnings'].append(
                            f"Agent {agent} requires {dep} but it's not executed before"
                        )
            else:
                validation['errors'].append(f"Unknown agent: {agent}")
                validation['is_valid'] = False
        
        # Check for circular dependencies
        for i, agent in enumerate(sequence):
            if agent in self.AVAILABLE_AGENTS:
                dependencies = self.AVAILABLE_AGENTS[agent]['dependencies']
                for dep in dependencies:
                    if dep in sequence[i:]:
                        validation['errors'].append(
                            f"Circular dependency detected: {agent} -> {dep}"
                        )
                        validation['is_valid'] = False
        
        return validation
    
    def should_execute_agent(
        self,
        agent_id: str,
        plan: Dict[str, Any],
        execution_results: Dict[str, Any]
    ) -> bool:
        """
        Determine if an agent should be executed based on conditional logic
        
        Args:
            agent_id: Agent to check
            plan: Execution plan
            execution_results: Results from previous agents
            
        Returns:
            True if agent should execute, False otherwise
        """
        conditional_logic = plan.get('conditional_logic', {})
        
        # Check if extraction failed
        if conditional_logic.get('if_extraction_fails') == 'skip_all_subsequent':
            if 'legal_extractor' in execution_results:
                if not execution_results['legal_extractor'].get('success', False):
                    return False
        
        # Check if no citations found
        if agent_id == 'citation_normalizer':
            if conditional_logic.get('if_no_citations') == 'skip_citation_normalization':
                extractor_result = execution_results.get('legal_extractor', {})
                data = extractor_result.get('data', {})
                citations = data.get('citations', [])
                if not citations or len(citations) == 0:
                    return False
        
        return True
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent"""
        return self.AVAILABLE_AGENTS.get(agent_id)
    
    def list_available_agents(self) -> Dict[str, Any]:
        """List all available agents"""
        return self.AVAILABLE_AGENTS.copy()

