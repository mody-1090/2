// عند تحميل الصفحة
document.addEventListener("DOMContentLoaded", () => {
    console.log("تم تحميل الصفحة بنجاح، و main.js يعمل!");
  
    // تفعيل/إلغاء وضع داكن
    const darkModeToggle = document.getElementById("darkModeToggle");
    if (darkModeToggle) {
      darkModeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
  
        // حفظ الحالة في LocalStorage
        const isDarkMode = document.body.classList.contains("dark-mode");
        localStorage.setItem("darkMode", isDarkMode ? "enabled" : "disabled");
      });
    }
  
    // استعادة الحالة من LocalStorage
    if (localStorage.getItem("darkMode") === "enabled") {
      document.body.classList.add("dark-mode");
    }
  });
  
  // دالة النسخ
  function copyToClipboard(button) {
      var input = button.previousElementSibling;
      input.select();
      input.setSelectionRange(0, 99999);
      document.execCommand("copy");
      button.innerText = "✅ تم النسخ";
      setTimeout(() => {
          button.innerText = "📋 نسخ الرابط";
      }, 2000);
  }

  function loadSection(section, pushState = true) {
    let endpoint = "/dashboard/" + section;

    document.getElementById("content-area").innerHTML = "<div class='loading'>⏳ جاري التحميل...</div>";

    fetch(endpoint)
      .then(response => response.text())
      .then(html => {
        document.getElementById("content-area").innerHTML = html;
        if (pushState) {
            history.pushState({ section: section }, "", "/dashboard/" + section);
        }
      })
      .catch(error => console.error("Error loading section:", error));
}

window.onpopstate = function(event) {
    if (event.state) {
        loadSection(event.state.section, false);
    }
};
