document.addEventListener("DOMContentLoaded", async () => {
  const sidebarRoot = document.getElementById("sidebar-root");
  if (!sidebarRoot) {
    return;
  }

  try {
    // Try multiple possible paths for the sidebar
    const paths = ['/static/sidebar.html', 'sidebar.html', '/ui/sidebar.html'];
    let sidebarHtml = null;
    
    for (const path of paths) {
      try {
        const response = await fetch(path);
        if (response.ok) {
          sidebarHtml = await response.text();
          break;
        }
      } catch (e) {
        // Try next path
        continue;
      }
    }
    
    if (sidebarHtml) {
      sidebarRoot.innerHTML = sidebarHtml;
      
      // Run sidebar highlighting script after content is loaded
      setTimeout(() => {
        highlightCurrentPage();
        initializeThemeIcon();
      }, 100);
    } else {
      console.error("Failed to load sidebar from all paths");
      // Fallback: create minimal sidebar with theme toggle
      sidebarRoot.innerHTML = `
        <aside class="hidden lg:sticky lg:top-0 lg:flex lg:h-screen lg:max-h-screen lg:flex-col overflow-hidden border-r border-white/10 bg-slate-950/80 backdrop-blur-xl">
          <div class="px-6 py-5 mt-12">
            <div class="flex items-center gap-3">
              <div class="grid h-12 w-12 place-items-center rounded-3xl bg-gradient-to-br from-indigo-500 to-cyan-400 shadow-[0_24px_80px_-40px_rgba(56,189,248,0.65)]">
                <svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L14.4 7.2L20 8L16 12L16.8 17.6L12 15.2L7.2 17.6L8 12L4 8L9.6 7.2L12 2Z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </div>
              <div>
                <p class="text-xs uppercase tracking-[0.35em] text-slate-400">Publication Assistant</p>
                <h1 class="text-lg font-semibold text-white">for AI Projects</h1>
              </div>
            </div>
          </div>
          <nav class="flex-1 space-y-2 px-4 pb-4">
            <a class="flex items-center gap-3 rounded-3xl bg-slate-900/70 px-4 py-3 text-slate-100 transition hover:bg-white/10" href="index.html" data-nav="home">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-sky-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Home</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="generate.html" data-nav="generate">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-sky-400">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Generate Article</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="projects.html" data-nav="projects">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-cyan-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Projects</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="history.html" data-nav="history">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-emerald-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">History</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="saved.html" data-nav="saved">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-fuchsia-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Saved</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="analytics.html" data-nav="analytics">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-amber-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Analytics</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="settings.html" data-nav="settings">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-pink-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Settings</span>
            </a>
            <a class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white" href="help.html" data-nav="help">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-rose-300">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
              </span>
              <span class="font-medium">Help</span>
            </a>
          </nav>
          <div class="px-4 pb-4 border-t border-white/10 pt-4">
            <button onclick="if(typeof ThemeManager !== 'undefined') ThemeManager.toggle();" class="flex items-center gap-3 rounded-3xl px-4 py-3 text-slate-300 transition hover:bg-white/10 hover:text-white w-full">
              <span class="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-800 text-yellow-300">
                <svg class="h-5 w-5 theme-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
                </svg>
              </span>
              <span class="font-medium">Toggle Theme</span>
            </button>
          </div>
        </aside>
      `;
      
      // Run highlighting for fallback sidebar
      setTimeout(() => {
        highlightCurrentPage();
        initializeThemeIcon();
      }, 100);
    }
  } catch (error) {
    console.error("Sidebar include error:", error);
  }
});

// Highlight current page in sidebar
function highlightCurrentPage() {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('[data-nav]');
  
  navLinks.forEach(link => {
    const nav = link.getAttribute('data-nav');
    if (nav === currentPage.replace('.html', '') || 
        (currentPage === '' && nav === 'home') ||
        (currentPage === 'index.html' && nav === 'home')) {
      link.classList.add('bg-slate-900/70', 'text-slate-100');
      link.classList.remove('text-slate-300');
    } else {
      link.classList.remove('bg-slate-900/70', 'text-slate-100');
      link.classList.add('text-slate-300');
    }
  });
}

// Initialize theme icon in sidebar
function initializeThemeIcon() {
  if (typeof ThemeManager !== 'undefined') {
    ThemeManager.updateToggleIcons();
  }
}
