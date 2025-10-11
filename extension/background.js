// Law Case Finder - Background Service Worker

// Extension installation and update handling
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Law Case Finder installed:', details);
  
  if (details.reason === 'install') {
    // Show welcome notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/icon48.png',
      title: 'Law Case Finder Installed',
      message: 'Click the extension icon to start analyzing legal documents!'
    });
  }
});

// Handle messages from popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background received message:', request);
  
  switch (request.type) {
    case 'GET_TAB_TEXT':
      handleGetTabText(sender, sendResponse);
      return true; // Keep message channel open for async response
      
    case 'HIGHLIGHT_TEXT':
      handleHighlightText(request.data, sender, sendResponse);
      return true;
      
    case 'ANALYZE_SELECTION':
      handleAnalyzeSelection(request.data, sendResponse);
      return true;
      
    case 'CHECK_SERVER_STATUS':
      handleCheckServerStatus(sendResponse);
      return true;
      
    default:
      console.log('Unknown message type:', request.type);
      sendResponse({ success: false, error: 'Unknown message type' });
  }
});

// Get text content from current tab
async function handleGetTabText(sender, sendResponse) {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.id) {
      sendResponse({ success: false, error: 'No active tab found' });
      return;
    }
    
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: extractPageText,
    });
    
    const text = results[0]?.result || '';
    sendResponse({ success: true, data: { text, url: tab.url } });
    
  } catch (error) {
    console.error('Error getting tab text:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Highlight text on current page
async function handleHighlightText(data, sender, sendResponse) {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.id) {
      sendResponse({ success: false, error: 'No active tab found' });
      return;
    }
    
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: highlightText,
      args: [data.text, data.className || 'law-case-finder-highlight']
    });
    
    sendResponse({ success: true });
    
  } catch (error) {
    console.error('Error highlighting text:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Handle text selection analysis
async function handleAnalyzeSelection(data, sendResponse) {
  try {
    // This would typically send the selected text to the analysis API
    // For now, we'll just pass it back to the popup
    sendResponse({ 
      success: true, 
      data: { 
        selectedText: data.text,
        timestamp: Date.now()
      }
    });
    
  } catch (error) {
    console.error('Error analyzing selection:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Check if backend server is running
async function handleCheckServerStatus(sendResponse) {
  try {
    const response = await fetch('http://localhost:3001/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (response.ok) {
      const data = await response.json();
      sendResponse({ success: true, data });
    } else {
      sendResponse({ 
        success: false, 
        error: `Server responded with status ${response.status}` 
      });
    }
    
  } catch (error) {
    console.error('Server health check failed:', error);
    sendResponse({ 
      success: false, 
      error: 'Backend server is not accessible. Please ensure it is running on port 3001.' 
    });
  }
}

// Functions to be injected into web pages

// Extract text content from page
function extractPageText() {
  // Remove script and style elements
  const scripts = document.querySelectorAll('script, style, noscript');
  scripts.forEach(el => el.remove());
  
  // Get main content areas (prioritize legal document containers)
  const selectors = [
    'article',
    'main',
    '.content',
    '.document',
    '.judgment',
    '.opinion',
    '.case-text',
    'body'
  ];
  
  let text = '';
  
  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) {
      text = element.innerText || element.textContent || '';
      if (text.length > 500) break; // Use first substantial content
    }
  }
  
  // Fallback to body text
  if (!text || text.length < 100) {
    text = document.body.innerText || document.body.textContent || '';
  }
  
  // Clean up the text
  text = text.replace(/\s+/g, ' ').trim();
  
  return text;
}

// Highlight text on page
function highlightText(searchText, className = 'law-case-finder-highlight') {
  // Remove existing highlights
  const existingHighlights = document.querySelectorAll(`.${className}`);
  existingHighlights.forEach(highlight => {
    const parent = highlight.parentNode;
    parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
    parent.normalize();
  });
  
  if (!searchText || searchText.length < 3) return;
  
  // Create tree walker to find text nodes
  const walker = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: (node) => {
        // Skip script and style elements
        if (node.parentElement.tagName === 'SCRIPT' || 
            node.parentElement.tagName === 'STYLE') {
          return NodeFilter.FILTER_REJECT;
        }
        
        // Only accept nodes that contain the search text
        return node.textContent.toLowerCase().includes(searchText.toLowerCase()) 
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
  
  // Highlight text in each node
  textNodes.forEach(textNode => {
    const parent = textNode.parentNode;
    const text = textNode.textContent;
    const regex = new RegExp(`(${escapeRegExp(searchText)})`, 'gi');
    
    if (regex.test(text)) {
      const highlightedHTML = text.replace(regex, `<mark class="${className}">$1</mark>`);
      const wrapper = document.createElement('span');
      wrapper.innerHTML = highlightedHTML;
      parent.replaceChild(wrapper, textNode);
    }
  });
  
  // Scroll to first highlight
  const firstHighlight = document.querySelector(`.${className}`);
  if (firstHighlight) {
    firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// Utility function to escape regex special characters
function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Context menu integration
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'analyze-selection',
    title: 'Analyze with Law Case Finder',
    contexts: ['selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'analyze-selection' && info.selectionText) {
    // Send selected text to popup for analysis
    chrome.runtime.sendMessage({
      type: 'ANALYZE_SELECTION',
      data: { text: info.selectionText, url: tab.url }
    });
    
    // Open popup
    chrome.action.openPopup();
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  // This is handled by the popup, but we can add additional logic here if needed
  console.log('Extension icon clicked on tab:', tab.url);
});

// Monitor tab changes to clear highlights
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Clear any existing highlights when page loads
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      function: () => {
        const highlights = document.querySelectorAll('.law-case-finder-highlight');
        highlights.forEach(highlight => {
          const parent = highlight.parentNode;
          parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
          parent.normalize();
        });
      }
    }).catch(() => {
      // Ignore errors (e.g., on chrome:// pages)
    });
  }
});
