document.addEventListener("DOMContentLoaded", async () => {
  const sidebarRoot = document.getElementById("sidebar-root");
  if (!sidebarRoot) {
    return;
  }

  try {
    const response = await fetch("/static/sidebar.html");
    if (!response.ok) {
      throw new Error("Failed to load sidebar");
    }
    sidebarRoot.innerHTML = await response.text();
  } catch (error) {
    console.error("Sidebar include error:", error);
  }
});
