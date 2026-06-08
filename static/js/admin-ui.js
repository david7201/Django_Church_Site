(function () {
    "use strict";

    function enhanceNavigation() {
        var currentPath = window.location.pathname;
        var main = document.getElementById("main");
        var sidebar = document.getElementById("nav-sidebar");
        var sidebarToggle = document.getElementById("toggle-nav-sidebar");

        function syncMobileSidebar() {
            if (window.innerWidth >= 768 || !main || !sidebar) {
                return;
            }
            var isOpen = main.classList.contains("shifted");
            sidebar.style.setProperty("display", isOpen ? "block" : "none", "important");
            sidebar.style.setProperty("transform", "none", "important");
            sidebar.setAttribute("aria-expanded", isOpen ? "true" : "false");
            if (sidebarToggle) {
                sidebarToggle.style.setProperty("left", isOpen ? "272px" : "0", "important");
                sidebarToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
            }
        }

        if (window.innerWidth < 768 && main && sidebar) {
            main.classList.remove("shifted");
            sidebar.setAttribute("aria-expanded", "false");
            window.localStorage.setItem("django.admin.navSidebarIsOpen", "false");
            syncMobileSidebar();
            if (sidebarToggle) {
                sidebarToggle.addEventListener("click", function () {
                    window.setTimeout(syncMobileSidebar, 0);
                });
            }
        }

        document.querySelectorAll(".mz-nav-list a").forEach(function (link) {
            var href = link.getAttribute("href");
            if (href && href !== "/" && currentPath.indexOf(href) === 0) {
                link.classList.add("is-active");
                link.setAttribute("aria-current", "page");
            }
        });

        var filter = document.getElementById("nav-filter");
        if (!filter) {
            return;
        }
        filter.addEventListener("input", function () {
            var query = filter.value.trim().toLowerCase();
            document.querySelectorAll(".mz-nav-list li").forEach(function (item) {
                item.hidden = query && item.textContent.toLowerCase().indexOf(query) === -1;
            });
            document.querySelectorAll(".mz-nav-label").forEach(function (label) {
                var list = label.nextElementSibling;
                if (!list || !list.classList.contains("mz-nav-list")) {
                    return;
                }
                var hasVisibleItem = Array.from(list.querySelectorAll("li")).some(function (item) {
                    return !item.hidden;
                });
                label.hidden = !hasVisibleItem;
                list.hidden = !hasVisibleItem;
            });
        });

        document.querySelectorAll(".mz-nav-list a").forEach(function (link) {
            link.addEventListener("click", function () {
                if (window.innerWidth < 768 && main) {
                    main.classList.remove("shifted");
                    window.localStorage.setItem("django.admin.navSidebarIsOpen", "false");
                    syncMobileSidebar();
                }
            });
        });
    }

    function enhanceTextareas() {
        document.querySelectorAll("textarea").forEach(function (textarea) {
            if (textarea.scrollHeight > textarea.clientHeight && textarea.value) {
                textarea.style.height = Math.min(textarea.scrollHeight + 2, 420) + "px";
            }
        });
    }

    function protectNewsletterSend() {
        var form = document.getElementById("changelist-form");
        if (!form) {
            return;
        }
        form.addEventListener("submit", function (event) {
            var action = form.querySelector('select[name="action"]');
            if (
                action &&
                action.value === "send_newsletters" &&
                !window.confirm("Send the selected newsletter now? This will email matching subscribers.")
            ) {
                event.preventDefault();
            }
        });
    }

    function enhanceVisibilityControls() {
        document.querySelectorAll(
            'input[type="checkbox"][name$="is_visible"], input[type="checkbox"][name^="show_"], input[type="checkbox"][name*="-show_"]'
        ).forEach(function (checkbox) {
            checkbox.classList.add("mz-visibility-toggle");
            checkbox.setAttribute(
                "aria-label",
                checkbox.checked ? "Shown on website" : "Hidden from website"
            );
            checkbox.title = checkbox.checked
                ? "Shown on website. Switch off to hide."
                : "Hidden from website. Switch on to show.";

            var row = checkbox.closest(".form-row");
            var state = row ? row.querySelector(".mz-visibility-state") : null;
            if (row && !state) {
                state = document.createElement("span");
                state.className = "mz-visibility-state";
                checkbox.insertAdjacentElement("afterend", state);
            }

            function updateState() {
                checkbox.setAttribute(
                    "aria-label",
                    checkbox.checked ? "Shown on website" : "Hidden from website"
                );
                checkbox.title = checkbox.checked
                    ? "Shown on website. Switch off to hide."
                    : "Hidden from website. Switch on to show.";
                if (state) {
                    state.textContent = checkbox.checked ? "Visible" : "Hidden";
                    state.classList.toggle("is-hidden", !checkbox.checked);
                }
            }

            checkbox.addEventListener("change", updateState);
            updateState();
        });
    }

    function initializeIcons() {
        if (window.FontAwesome && window.FontAwesome.dom) {
            window.FontAwesome.dom.i2svg();
        }
    }

    function setupAutoDismissMessages() {
        document.querySelectorAll("ul.messagelist li").forEach(function (message) {
            window.setTimeout(function () {
                message.classList.add("is-dismissing");
                window.setTimeout(function () {
                    message.remove();
                    var list = document.querySelector("ul.messagelist");
                    if (list && !list.querySelector("li")) {
                        list.remove();
                    }
                }, 300);
            }, 5000);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        enhanceNavigation();
        enhanceTextareas();
        enhanceVisibilityControls();
        protectNewsletterSend();
        setupAutoDismissMessages();
        initializeIcons();
    });
})();
