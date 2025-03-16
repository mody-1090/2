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

 
