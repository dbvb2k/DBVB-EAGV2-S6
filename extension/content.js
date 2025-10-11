// Law Case Finder - Content Script

(function() {
  'use strict';
  
  // Avoid running multiple times on the same page
  if (window.lawCaseFinderContentScript) return;
  window.lawCaseFinderContentScript = true;

  console.log('Law Case Finder content script loaded');

  // Configuration
  const CONFIG = {
    highlightClass: 'law-case-finder-highlight',
    floatingButtonId: 'law-case-finder-floating-btn',
    selectionMinLength: 10
  };

  // State management
  let isFloatingButtonVisible = false;
  let currentSelection = null;
  let highlightedElements = [];

  // Initialize content script
  function initialize() {
    createFloatingButton();
    setupSelectionHandler();
    setupMessageListener();
    injectStyles();
    
    // Check if this looks like a legal document page
    if (isLegalDocumentPage()) {
      showFloatingButton();
    }
  }

  // Create floating analysis button
  function createFloatingButton() {
    if (document.getElementById(CONFIG.floatingButtonId)) return;

    const button = document.createElement('button');
    button.id = CONFIG.floatingButtonId;
    button.innerHTML = '⚖️ Analyze';
    button.title = 'Analyze this legal document with Law Case Finder';
    button.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
      color: white;
      border: none;
      border-radius: 25px;
      padding: 12px 20px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(42, 82, 152, 0.3);
      transition: all 0.3s ease;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      display: none;
    `;

    button.addEventListener('click', handleFloatingButtonClick);
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 6px 20px rgba(42, 82, 152, 0.4)';
    });
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translateY(0)';
      button.style.boxShadow = '0 4px 15px rgba(42, 82, 152, 0.3)';
    });

    document.body.appendChild(button);
  }

  // Setup text selection handler
  function setupSelectionHandler() {
    document.addEventListener('mouseup', handleTextSelection);
    document.addEventListener('keyup', handleTextSelection);
  }

  // Setup message listener for communication with background script
  function setupMessageListener() {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      switch (request.type) {
        case 'HIGHLIGHT_TEXT':
          highlightText(request.data.text, request.data.options);
          sendResponse({ success: true });
          break;
        case 'CLEAR_HIGHLIGHTS':
          clearHighlights();
          sendResponse({ success: true });
          break;
        case 'GET_SELECTION':
          sendResponse({ 
            success: true, 
            data: { text: getSelectedText() }
          });
          break;
        case 'EXTRACT_PAGE_TEXT':
          sendResponse({ 
            success: true, 
            data: { text: extractPageText() }
          });
          break;
        default:
          sendResponse({ success: false, error: 'Unknown message type' });
      }
    });
  }

  // Inject CSS styles for highlights and UI elements
  function injectStyles() {
    if (document.getElementById('law-case-finder-styles')) return;

    const style = document.createElement('style');
    style.id = 'law-case-finder-styles';
    style.textContent = `
      .${CONFIG.highlightClass} {
        background-color: #fff3cd !important;
        border: 1px solid #ffeaa7 !important;
        border-radius: 2px !important;
        padding: 1px 2px !important;
        margin: 0 1px !important;
        box-shadow: 0 1px 3px rgba(255, 193, 7, 0.3) !important;
        transition: all 0.2s ease !important;
      }
      
      .${CONFIG.highlightClass}:hover {
        background-color: #ffeaa7 !important;
        box-shadow: 0 2px 5px rgba(255, 193, 7, 0.5) !important;
      }
      
      .law-case-finder-selection-tooltip {
        position: absolute;
        background: #2a5298;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        z-index: 10001;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      }
      
      .law-case-finder-selection-tooltip:hover {
        background: #1e3c72;
        transform: translateY(-1px);
      }
      
      .law-case-finder-selection-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 5px solid transparent;
        border-top-color: #2a5298;
      }
    `;
    
    document.head.appendChild(style);
  }

  // Check if current page appears to be a legal document
  function isLegalDocumentPage() {
    const url = window.location.href.toLowerCase();
    const title = document.title.toLowerCase();
    const content = document.body.textContent.toLowerCase();

    // URL patterns that suggest legal content
    const legalUrlPatterns = [
      'court', 'judgment', 'opinion', 'case', 'legal', 'law',
      'supreme', 'tribunal', 'appeal', 'litigation', 'ruling'
    ];

    // Content patterns that suggest legal documents
    const legalContentPatterns = [
      'plaintiff', 'defendant', 'court', 'judgment', 'opinion',
      'holding', 'reasoning', 'citation', 'statute', 'constitutional',
      'appeal', 'motion', 'order', 'injunction', 'damages'
    ];

    // Check URL
    const urlMatches = legalUrlPatterns.some(pattern => url.includes(pattern));
    
    // Check title
    const titleMatches = legalUrlPatterns.some(pattern => title.includes(pattern));
    
    // Check content (sample first 2000 characters)
    const contentSample = content.substring(0, 2000);
    const contentMatches = legalContentPatterns.filter(pattern => 
      contentSample.includes(pattern)
    ).length;

    // Return true if we have URL/title match OR multiple content matches
    return urlMatches || titleMatches || contentMatches >= 3;
  }

  // Handle floating button click
  function handleFloatingButtonClick() {
    const pageText = extractPageText();
    
    if (pageText.length < 100) {
      alert('This page does not contain enough text for analysis.');
      return;
    }

    // Send message to background script to open popup with page text
    chrome.runtime.sendMessage({
      type: 'ANALYZE_PAGE_TEXT',
      data: { 
        text: pageText,
        url: window.location.href,
        title: document.title
      }
    });
  }

  // Handle text selection
  function handleTextSelection() {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    // Remove existing selection tooltip
    removeSelectionTooltip();

    if (selectedText.length >= CONFIG.selectionMinLength) {
      currentSelection = selectedText;
      showSelectionTooltip(selection);
    } else {
      currentSelection = null;
    }
  }

  // Show tooltip for text selection
  function showSelectionTooltip(selection) {
    if (selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    const tooltip = document.createElement('div');
    tooltip.className = 'law-case-finder-selection-tooltip';
    tooltip.textContent = '⚖️ Analyze Selection';
    tooltip.addEventListener('click', handleSelectionAnalysis);

    // Position tooltip above selection
    tooltip.style.left = `${rect.left + (rect.width / 2)}px`;
    tooltip.style.top = `${rect.top - 35 + window.scrollY}px`;
    tooltip.style.transform = 'translateX(-50%)';

    document.body.appendChild(tooltip);

    // Remove tooltip after 5 seconds
    setTimeout(() => {
      removeSelectionTooltip();
    }, 5000);
  }

  // Remove selection tooltip
  function removeSelectionTooltip() {
    const tooltip = document.querySelector('.law-case-finder-selection-tooltip');
    if (tooltip) {
      tooltip.remove();
    }
  }

  // Handle selection analysis
  function handleSelectionAnalysis() {
    if (!currentSelection) return;

    removeSelectionTooltip();

    // Send selected text to background script
    chrome.runtime.sendMessage({
      type: 'ANALYZE_SELECTION',
      data: { 
        text: currentSelection,
        url: window.location.href,
        title: document.title
      }
    });
  }

  // Extract text from page
  function extractPageText() {
    // Try to find main content area
    const contentSelectors = [
      'article',
      'main',
      '[role="main"]',
      '.content',
      '.document',
      '.judgment',
      '.opinion',
      '.case-text',
      '#content',
      '.main-content'
    ];

    let text = '';

    for (const selector of contentSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        text = element.innerText || element.textContent || '';
        if (text.length > 500) break;
      }
    }

    // Fallback to body text if no main content found
    if (!text || text.length < 100) {
      text = document.body.innerText || document.body.textContent || '';
    }

    // Clean up text
    text = text.replace(/\s+/g, ' ').trim();
    
    // Remove common navigation and footer content
    const linesToRemove = text.split('\n').filter(line => {
      const lowerLine = line.toLowerCase().trim();
      return !lowerLine.includes('cookie') &&
             !lowerLine.includes('navigation') &&
             !lowerLine.includes('menu') &&
             !lowerLine.includes('footer') &&
             !lowerLine.includes('copyright') &&
             line.trim().length > 10;
    });

    return linesToRemove.join('\n');
  }

  // Get currently selected text
  function getSelectedText() {
    return window.getSelection().toString().trim();
  }

  // Highlight text on page
  function highlightText(searchText, options = {}) {
    if (!searchText || searchText.length < 3) return;

    clearHighlights();

    const className = options.className || CONFIG.highlightClass;
    const caseSensitive = options.caseSensitive || false;
    const wholeWords = options.wholeWords || false;

    // Create regex pattern
    let pattern = escapeRegExp(searchText);
    if (wholeWords) {
      pattern = `\\b${pattern}\\b`;
    }
    
    const flags = caseSensitive ? 'g' : 'gi';
    const regex = new RegExp(`(${pattern})`, flags);

    // Find and highlight text
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: (node) => {
          // Skip script, style, and already highlighted elements
          const parent = node.parentElement;
          if (parent.tagName === 'SCRIPT' || 
              parent.tagName === 'STYLE' ||
              parent.classList.contains(className)) {
            return NodeFilter.FILTER_REJECT;
          }
          
          return regex.test(node.textContent) 
            ? NodeFilter.FILTER_ACCEPT 
            : NodeFilter.FILTER_REJECT;
        }
      }
    );

    const textNodes = [];
    let node;
    
    while (node = walker.nextNode()) {
      textNodes.push(node);
    }

    // Apply highlights
    textNodes.forEach(textNode => {
      const parent = textNode.parentNode;
      const text = textNode.textContent;
      
      if (regex.test(text)) {
        const highlightedHTML = text.replace(regex, `<mark class="${className}">$1</mark>`);
        const wrapper = document.createElement('span');
        wrapper.innerHTML = highlightedHTML;
        
        // Replace text node with highlighted content
        parent.replaceChild(wrapper, textNode);
        
        // Track highlighted elements for cleanup
        const highlights = wrapper.querySelectorAll(`.${className}`);
        highlightedElements.push(...highlights);
      }
    });

    // Scroll to first highlight
    if (highlightedElements.length > 0) {
      highlightedElements[0].scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
    }

    return highlightedElements.length;
  }

  // Clear all highlights
  function clearHighlights() {
    highlightedElements.forEach(element => {
      const parent = element.parentNode;
      if (parent) {
        parent.replaceChild(document.createTextNode(element.textContent), element);
        parent.normalize();
      }
    });
    
    highlightedElements = [];
  }

  // Show floating button
  function showFloatingButton() {
    const button = document.getElementById(CONFIG.floatingButtonId);
    if (button) {
      button.style.display = 'block';
      isFloatingButtonVisible = true;
    }
  }

  // Hide floating button
  function hideFloatingButton() {
    const button = document.getElementById(CONFIG.floatingButtonId);
    if (button) {
      button.style.display = 'none';
      isFloatingButtonVisible = false;
    }
  }

  // Utility function to escape regex special characters
  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  // Handle page visibility changes
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      removeSelectionTooltip();
    }
  });

  // Handle page navigation
  window.addEventListener('beforeunload', () => {
    clearHighlights();
    removeSelectionTooltip();
  });

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }

})();
