// Shared JavaScript utilities for the Publication Assistant UI

// Theme Management
const ThemeManager = {
  currentTheme: 'dark',
  
  init() {
    const stored = localStorage.getItem('theme');
    if (stored) {
      this.currentTheme = stored;
    }
    this.applyTheme();
  },
  
  toggle() {
    this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', this.currentTheme);
    this.applyTheme();
  },
  
  applyTheme() {
    const html = document.documentElement;
    if (this.currentTheme === 'dark') {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
    this.updateToggleIcons();
  },
  
  updateToggleIcons() {
    const toggles = document.querySelectorAll('[data-theme-toggle]');
    toggles.forEach(toggle => {
      const icon = toggle.querySelector('.theme-icon');
      if (icon) {
        icon.innerHTML = this.currentTheme === 'dark' 
          ? '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>'
          : '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9 9 0 0018 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';
      }
    });
  }
};

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
});

// API Client with error handling and retry
const APIClient = {
  async fetch(url, options = {}) {
    const maxRetries = 3;
    let lastError;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        lastError = error;
        if (attempt < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
        }
      }
    }
    
    throw lastError;
  },
  
  async get(endpoint) {
    return this.fetch(endpoint);
  },
  
  async post(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  async delete(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'DELETE',
      body: JSON.stringify(data),
    });
  },
  
  async put(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }
};

// Notification System
const NotificationManager = {
  container: null,
  
  init() {
    this.container = document.createElement('div');
    this.container.id = 'notification-container';
    this.container.className = 'fixed top-4 right-4 z-50 space-y-2';
    document.body.appendChild(this.container);
  },
  
  show(message, type = 'info', duration = 5000) {
    if (!this.container) this.init();
    
    const notification = document.createElement('div');
    const colors = {
      info: 'bg-blue-500/10 border-blue-500/50 text-blue-400',
      success: 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400',
      error: 'bg-red-500/10 border-red-500/50 text-red-400',
      warning: 'bg-amber-500/10 border-amber-500/50 text-amber-400'
    };
    
    notification.className = `rounded-xl border px-4 py-3 shadow-lg backdrop-blur-xl ${colors[type]} flex items-center gap-3 min-w-[300px] animate-in slide-in-from-right`;
    notification.innerHTML = `
      <span class="text-sm font-medium">${message}</span>
      <button onclick="this.parentElement.remove()" class="opacity-60 hover:opacity-100 transition-opacity">
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    `;
    
    this.container.appendChild(notification);
    
    setTimeout(() => {
      notification.classList.add('animate-out', 'slide-out-to-right');
      setTimeout(() => notification.remove(), 300);
    }, duration);
  }
};

// Loading State Manager
const LoadingManager = {
  show(element, message = 'Loading...') {
    element.innerHTML = `
      <div class="flex flex-col items-center justify-center py-12 space-y-4">
        <div class="animate-spin h-8 w-8 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
        <p class="text-sm text-slate-400">${message}</p>
      </div>
    `;
  },
  
  hide(element, content) {
    element.innerHTML = content;
  }
};

// Skeleton Loader Generator
const SkeletonLoader = {
  card() {
    return `
      <div class="animate-pulse space-y-4">
        <div class="h-4 bg-slate-700 rounded w-3/4"></div>
        <div class="h-4 bg-slate-700 rounded w-1/2"></div>
        <div class="h-32 bg-slate-700 rounded-lg"></div>
      </div>
    `;
  },
  
  text() {
    return `
      <div class="animate-pulse space-y-2">
        <div class="h-4 bg-slate-700 rounded"></div>
        <div class="h-4 bg-slate-700 rounded w-5/6"></div>
        <div class="h-4 bg-slate-700 rounded w-4/6"></div>
      </div>
    `;
  }
};

// Mobile Menu Manager
const MobileMenu = {
  isOpen: false,
  
  init() {
    this.createButton();
    this.createOverlay();
  },
  
  createButton() {
    const button = document.createElement('button');
    button.className = 'lg:hidden fixed top-4 right-4 z-50 p-2 rounded-xl bg-slate-800 border border-slate-700 text-white';
    button.innerHTML = `
      <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
      </svg>
    `;
    button.onclick = () => this.toggle();
    document.body.appendChild(button);
  },
  
  createOverlay() {
    this.overlay = document.createElement('div');
    this.overlay.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-40 hidden';
    this.overlay.onclick = () => this.close();
    document.body.appendChild(this.overlay);
  },
  
  toggle() {
    this.isOpen = !this.isOpen;
    const sidebar = document.querySelector('aside');
    
    if (this.isOpen) {
      sidebar.classList.remove('hidden');
      sidebar.classList.add('fixed', 'inset-0', 'z-50', 'bg-slate-950');
      this.overlay.classList.remove('hidden');
    } else {
      sidebar.classList.add('hidden');
      sidebar.classList.remove('fixed', 'inset-0', 'z-50', 'bg-slate-950');
      this.overlay.classList.add('hidden');
    }
  },
  
  close() {
    this.isOpen = false;
    const sidebar = document.querySelector('aside');
    sidebar.classList.add('hidden');
    sidebar.classList.remove('fixed', 'inset-0', 'z-50', 'bg-slate-950');
    this.overlay.classList.add('hidden');
  }
};

// Markdown Renderer (using marked library)
const MarkdownRenderer = {
  async init() {
    if (typeof marked === 'undefined') {
      await this.loadLibrary();
    }
  },
  
  async loadLibrary() {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
      script.onload = resolve;
      document.head.appendChild(script);
    });
  },
  
  render(markdown) {
    if (typeof marked === 'undefined') {
      return `<pre class="bg-slate-800 p-4 rounded-lg overflow-x-auto">${markdown}</pre>`;
    }
    return marked.parse(markdown);
  }
};

// Agent Pipeline Visualizer
const PipelineVisualizer = {
  steps: [
    { id: 'repo_analyzer', name: 'Repository Analyzer', icon: '🔍' },
    { id: 'metadata_recommender', name: 'Metadata Recommender', icon: '🏷️' },
    { id: 'content_improver', name: 'Content Improver', icon: '✍️' },
    { id: 'reviewer_critic', name: 'Reviewer & Critic', icon: '🧐' },
    { id: 'fact_checker', name: 'Fact Checker', icon: '📚' }
  ],
  
  render(activeStep = null, completedSteps = []) {
    return `
      <div class="space-y-3">
        ${this.steps.map((step, index) => {
          const isActive = step.id === activeStep;
          const isCompleted = completedSteps.includes(step.id);
          const isPending = !isActive && !isCompleted;
          
          const statusColors = {
            active: 'border-indigo-500 bg-indigo-500/10 text-indigo-400',
            completed: 'border-emerald-500 bg-emerald-500/10 text-emerald-400',
            pending: 'border-slate-600 bg-slate-800/50 text-slate-500'
          };
          
          const statusIcon = {
            active: '<div class="animate-spin h-4 w-4 border-2 border-indigo-500 border-t-transparent rounded-full"></div>',
            completed: '<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
            pending: '<div class="h-4 w-4 rounded-full border-2 border-slate-600"></div>'
          };
          
          return `
            <div class="flex items-center gap-3 p-3 rounded-xl border ${statusColors[isActive ? 'active' : isCompleted ? 'completed' : 'pending']} transition-all duration-300">
              <div class="flex-shrink-0 w-8 h-8 flex items-center justify-center">
                ${statusIcon[isActive ? 'active' : isCompleted ? 'completed' : 'pending']}
              </div>
              <div class="flex items-center gap-2">
                <span class="text-lg">${step.icon}</span>
                <span class="font-medium text-sm">${step.name}</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }
};

// Initialize all managers when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  NotificationManager.init();
  MobileMenu.init();
  MarkdownRenderer.init();
  
  // Make globally available
  window.ThemeManager = ThemeManager;
  window.NotificationManager = NotificationManager;
  window.LoadingManager = LoadingManager;
  window.SkeletonLoader = SkeletonLoader;
  window.PipelineVisualizer = PipelineVisualizer;
  window.APIClient = APIClient;
  window.ClipboardManager = ClipboardManager;
  window.FormValidator = FormValidator;
  window.DateFormatter = DateFormatter;
  window.debounce = debounce;
});

// Copy to Clipboard Utility
const ClipboardManager = {
  async copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    try {
      await navigator.clipboard.writeText(text);
      NotificationManager.show(successMessage, 'success');
      return true;
    } catch (error) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        NotificationManager.show(successMessage, 'success');
        return true;
      } catch (fallbackError) {
        NotificationManager.show('Failed to copy to clipboard', 'error');
        return false;
      } finally {
        document.body.removeChild(textArea);
      }
    }
  }
};

// Form Validation Utility
const FormValidator = {
  validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },
  
  validateUrl(url) {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },
  
  validateRequired(value) {
    return value !== null && value !== undefined && value.trim() !== '';
  }
};

// Date Formatting Utility
const DateFormatter = {
  formatRelative(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 7) {
      return new Date(date).toLocaleDateString();
    } else if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (minutes > 0) {
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  },
  
  formatFull(date) {
    return new Date(date).toLocaleString();
  }
};

// Debounce Utility
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};