(() => {
    "use strict";

    const root = document.documentElement;
    const messages = window.trellarMessages || {};
    const csrfToken = messages.csrfToken || "";

    const postJson = async (url, payload) => {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-Token": csrfToken,
            },
            body: JSON.stringify(payload),
        });

        const contentType = response.headers.get("content-type") || "";
        const data = contentType.includes("application/json") ? await response.json() : {};
        if (!response.ok || data.ok === false) {
            throw new Error(data.error || `request_failed_${response.status}`);
        }
        return data;
    };

    const isInputLike = (node) => {
        if (!node || !(node instanceof HTMLElement)) {
            return false;
        }
        const tag = node.tagName.toLowerCase();
        return tag === "input" || tag === "textarea" || tag === "select" || node.isContentEditable;
    };

    const preferencesDefaults = {
        theme: "system",
        contrast: "default",
        text: "default",
        motion: "default",
    };

    const preferencesKey = "trellar.preferences";

    const readPreferences = () => {
        try {
            const raw = localStorage.getItem(preferencesKey);
            if (!raw) {
                return { ...preferencesDefaults };
            }
            const parsed = JSON.parse(raw);
            return {
                theme: parsed.theme || preferencesDefaults.theme,
                contrast: parsed.contrast || preferencesDefaults.contrast,
                text: parsed.text || preferencesDefaults.text,
                motion: parsed.motion || preferencesDefaults.motion,
            };
        } catch (_error) {
            return { ...preferencesDefaults };
        }
    };

    const savePreferences = (prefs) => {
        localStorage.setItem(preferencesKey, JSON.stringify(prefs));
    };

    const applyPreferences = (prefs) => {
        root.classList.remove("theme-dark", "theme-light", "contrast-more", "text-large", "motion-reduce");

        if (prefs.theme === "dark") {
            root.classList.add("theme-dark");
        }

        if (prefs.theme === "light") {
            root.classList.add("theme-light");
        }

        if (prefs.contrast === "more") {
            root.classList.add("contrast-more");
        }

        if (prefs.text === "large") {
            root.classList.add("text-large");
        }

        if (prefs.motion === "reduce") {
            root.classList.add("motion-reduce");
        }
    };

    const syncPreferenceInputs = (prefs) => {
        document.querySelectorAll("[data-pref]").forEach((input) => {
            const key = input.getAttribute("data-pref");
            if (!key || !(key in prefs)) {
                return;
            }
            input.value = prefs[key];
        });
    };

    const initializePreferences = () => {
        const toggle = document.getElementById("prefs-toggle");
        const panel = document.getElementById("prefs-panel");
        const saveButton = document.getElementById("prefs-save");

        const prefs = readPreferences();
        applyPreferences(prefs);
        syncPreferenceInputs(prefs);

        if (toggle && panel) {
            toggle.addEventListener("click", () => {
                const expanded = toggle.getAttribute("aria-expanded") === "true";
                toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
                panel.hidden = expanded;
            });
        }

        if (saveButton) {
            saveButton.addEventListener("click", () => {
                const nextPrefs = { ...preferencesDefaults };
                document.querySelectorAll("[data-pref]").forEach((input) => {
                    const key = input.getAttribute("data-pref");
                    if (key) {
                        nextPrefs[key] = input.value;
                    }
                });
                savePreferences(nextPrefs);
                applyPreferences(nextPrefs);
            });
        }
    };

    const initializeNavToggle = () => {
        const toggle = document.getElementById("nav-toggle");
        const nav = document.getElementById("site-nav");

        if (!toggle || !nav) {
            return;
        }

        const query = window.matchMedia("(max-width: 768px)");

        const sync = () => {
            if (query.matches) {
                const expanded = toggle.getAttribute("aria-expanded") === "true";
                nav.hidden = !expanded;
            } else {
                nav.hidden = false;
                toggle.setAttribute("aria-expanded", "false");
            }
        };

        toggle.addEventListener("click", () => {
            const expanded = toggle.getAttribute("aria-expanded") === "true";
            toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
            nav.hidden = expanded;
        });

        if (typeof query.addEventListener === "function") {
            query.addEventListener("change", sync);
        } else {
            query.addListener(sync);
        }

        sync();
    };

    const initializeFoldables = () => {
        document.querySelectorAll("[data-toggle-target]").forEach((button) => {
            button.addEventListener("click", () => {
                const targetId = button.getAttribute("data-toggle-target");
                if (!targetId) {
                    return;
                }
                const target = document.getElementById(targetId);
                if (!target) {
                    return;
                }

                const expanded = button.getAttribute("aria-expanded") === "true";
                button.setAttribute("aria-expanded", expanded ? "false" : "true");
                target.hidden = expanded;
            });
        });
    };

    const initializeDismissableFlash = () => {
        document.querySelectorAll("[data-dismiss-flash]").forEach((button) => {
            button.addEventListener("click", () => {
                const flash = button.closest(".flash");
                if (flash) {
                    flash.remove();
                }
            });
        });
    };

    const updateCharacterCounter = (field) => {
        const counterId = field.getAttribute("data-char-count");
        if (!counterId) {
            return;
        }

        const counter = document.getElementById(counterId);
        if (!counter) {
            return;
        }

        const max = Number(field.getAttribute("maxlength")) || 0;
        const length = field.value.length;
        counter.textContent = max > 0 ? `${length}/${max}` : `${length}`;
    };

    const initializeCharacterCounters = () => {
        document.querySelectorAll("[data-char-count]").forEach((field) => {
            updateCharacterCounter(field);
            field.addEventListener("input", () => updateCharacterCounter(field));
        });
    };

    const initializeSavingAnnouncements = () => {
        document.querySelectorAll("form").forEach((form) => {
            form.addEventListener("submit", () => {
                if ((form.method || "").toLowerCase() !== "post") {
                    return;
                }
                const status = form.querySelector(".status-message[role='status']");
                if (status) {
                    status.textContent = messages.statusSaving || "Saving...";
                }
            });
        });
    };

    const modalElements = {
        overlay: document.getElementById("confirm-modal"),
        message: document.getElementById("confirm-message"),
        accept: document.getElementById("confirm-accept"),
        cancel: document.getElementById("confirm-cancel"),
    };

    let modalConfirmAction = null;
    let modalRestoreFocus = null;

    const trapFocusInModal = (event) => {
        if (event.key !== "Tab" || !modalElements.overlay || modalElements.overlay.hidden) {
            return;
        }

        const focusables = modalElements.overlay.querySelectorAll(
            "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        );
        if (!focusables.length) {
            return;
        }

        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    };

    const closeConfirmModal = () => {
        if (!modalElements.overlay) {
            return;
        }
        modalElements.overlay.hidden = true;
        document.removeEventListener("keydown", trapFocusInModal);
        if (modalRestoreFocus) {
            modalRestoreFocus.focus();
        }
        modalConfirmAction = null;
        modalRestoreFocus = null;
    };

    const openConfirmModal = (message, onConfirm, trigger) => {
        if (!modalElements.overlay || !modalElements.message || !modalElements.accept || !modalElements.cancel) {
            return;
        }

        modalConfirmAction = onConfirm;
        modalRestoreFocus = trigger || null;
        modalElements.message.textContent = message;
        modalElements.overlay.hidden = false;
        modalElements.accept.focus();

        document.addEventListener("keydown", trapFocusInModal);
    };

    const initializeConfirmModal = () => {
        if (!modalElements.overlay || !modalElements.accept || !modalElements.cancel) {
            return;
        }

        modalElements.accept.addEventListener("click", () => {
            if (typeof modalConfirmAction === "function") {
                modalConfirmAction();
            }
            closeConfirmModal();
        });

        modalElements.cancel.addEventListener("click", closeConfirmModal);

        modalElements.overlay.addEventListener("click", (event) => {
            if (event.target === modalElements.overlay) {
                closeConfirmModal();
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && modalElements.overlay && !modalElements.overlay.hidden) {
                closeConfirmModal();
            }
        });

        document.addEventListener("click", (event) => {
            const resetButton = event.target.closest("button[type='reset'][data-confirm]");
            if (!resetButton) {
                return;
            }

            event.preventDefault();
            const message = resetButton.getAttribute("data-confirm") || "Confirm?";
            openConfirmModal(message, () => {
                if (resetButton.form) {
                    resetButton.form.reset();
                    resetButton.form
                        .querySelectorAll("[data-char-count]")
                        .forEach((field) => updateCharacterCounter(field));
                }
            }, resetButton);
        });
    };

    const editorElements = {
        overlay: document.getElementById("editor-modal"),
        title: document.getElementById("editor-title"),
        description: document.getElementById("editor-description"),
        error: document.getElementById("editor-error"),
        form: document.getElementById("editor-form"),
        primaryLabel: document.getElementById("editor-primary-label"),
        primaryInput: document.getElementById("editor-primary-input"),
        secondaryLabel: document.getElementById("editor-secondary-label"),
        secondaryInput: document.getElementById("editor-secondary-input"),
        submit: document.getElementById("editor-submit"),
        cancel: document.getElementById("editor-cancel"),
    };

    let editorRestoreFocus = null;
    let editorSubmitAction = null;

    const trapFocusInEditorModal = (event) => {
        if (event.key !== "Tab" || !editorElements.overlay || editorElements.overlay.hidden) {
            return;
        }

        const focusables = editorElements.overlay.querySelectorAll(
            "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
        );
        if (!focusables.length) {
            return;
        }

        const first = focusables[0];
        const last = focusables[focusables.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    };

    const hideEditorError = () => {
        if (!editorElements.error) {
            return;
        }
        editorElements.error.hidden = true;
        editorElements.error.textContent = "";
    };

    const showEditorError = (message) => {
        if (!editorElements.error) {
            return;
        }
        editorElements.error.textContent = message;
        editorElements.error.hidden = false;
    };

    const closeEditorModal = () => {
        if (
            !editorElements.overlay ||
            !editorElements.form ||
            !editorElements.primaryInput ||
            !editorElements.secondaryInput ||
            !editorElements.submit
        ) {
            return;
        }

        editorElements.overlay.hidden = true;
        editorElements.form.reset();
        editorElements.primaryInput.removeAttribute("maxlength");
        editorElements.secondaryInput.removeAttribute("maxlength");
        editorElements.submit.removeAttribute("aria-busy");
        editorElements.submit.disabled = false;
        hideEditorError();
        editorSubmitAction = null;
        document.removeEventListener("keydown", trapFocusInEditorModal);

        if (editorRestoreFocus) {
            editorRestoreFocus.focus();
        }
        editorRestoreFocus = null;
    };

    const openEditorModal = (config) => {
        if (
            !editorElements.overlay ||
            !editorElements.title ||
            !editorElements.description ||
            !editorElements.form ||
            !editorElements.primaryLabel ||
            !editorElements.primaryInput ||
            !editorElements.secondaryLabel ||
            !editorElements.secondaryInput ||
            !editorElements.submit
        ) {
            return;
        }

        editorSubmitAction = config.onSubmit;
        editorRestoreFocus = config.trigger || null;

        editorElements.title.textContent = config.title || "";
        editorElements.description.textContent = config.description || "";
        editorElements.primaryLabel.textContent = config.primaryLabel || "";
        editorElements.secondaryLabel.textContent = config.secondaryLabel || "";
        editorElements.submit.textContent = config.submitLabel || (messages.commonCreate || "Create");

        editorElements.primaryInput.value = config.primaryValue || "";
        editorElements.secondaryInput.value = config.secondaryValue || "";

        if (config.primaryMaxLength) {
            editorElements.primaryInput.setAttribute("maxlength", String(config.primaryMaxLength));
        } else {
            editorElements.primaryInput.removeAttribute("maxlength");
        }

        if (config.secondaryMaxLength) {
            editorElements.secondaryInput.setAttribute("maxlength", String(config.secondaryMaxLength));
        } else {
            editorElements.secondaryInput.removeAttribute("maxlength");
        }

        hideEditorError();
        editorElements.overlay.hidden = false;
        editorElements.primaryInput.focus();
        document.addEventListener("keydown", trapFocusInEditorModal);
    };

    const initializeEditorModal = () => {
        if (
            !editorElements.overlay ||
            !editorElements.form ||
            !editorElements.primaryInput ||
            !editorElements.secondaryInput ||
            !editorElements.submit ||
            !editorElements.cancel
        ) {
            return;
        }

        editorElements.form.addEventListener("submit", async (event) => {
            event.preventDefault();

            if (typeof editorSubmitAction !== "function") {
                return;
            }

            const primaryValue = editorElements.primaryInput.value.trim();
            const secondaryValue = editorElements.secondaryInput.value.trim();

            if (!primaryValue) {
                showEditorError(messages.errorRequired || "This field is required.");
                editorElements.primaryInput.focus();
                return;
            }

            hideEditorError();
            editorElements.submit.disabled = true;
            editorElements.submit.setAttribute("aria-busy", "true");

            try {
                const shouldClose = await editorSubmitAction({
                    primary: primaryValue,
                    secondary: secondaryValue,
                    setError: showEditorError,
                });
                if (shouldClose !== false) {
                    closeEditorModal();
                }
            } finally {
                editorElements.submit.disabled = false;
                editorElements.submit.removeAttribute("aria-busy");
            }
        });

        editorElements.cancel.addEventListener("click", closeEditorModal);

        editorElements.overlay.addEventListener("click", (event) => {
            if (event.target === editorElements.overlay) {
                closeEditorModal();
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && editorElements.overlay && !editorElements.overlay.hidden) {
                closeEditorModal();
            }
        });
    };

    const toastStack = document.getElementById("toast-stack");

    const showUndoToast = (message, onUndo) => {
        if (!toastStack) {
            return;
        }

        const toast = document.createElement("article");
        toast.className = "toast";

        const text = document.createElement("p");
        text.textContent = message;

        const undoButton = document.createElement("button");
        undoButton.type = "button";
        undoButton.className = "button button-ghost";
        undoButton.textContent = messages.undo || "Undo";

        undoButton.addEventListener("click", () => {
            if (typeof onUndo === "function") {
                onUndo();
            }
            toast.remove();
            const live = document.getElementById("board-live");
            if (live) {
                live.textContent = messages.boardUndoDone || "Action undone.";
            }
        });

        toast.append(text, undoButton);
        toastStack.append(toast);

        window.setTimeout(() => {
            toast.remove();
        }, 8000);
    };

    const initializeLocalizedTimes = () => {
        const language = root.lang || undefined;
        const absoluteFormatter = new Intl.DateTimeFormat(language, {
            dateStyle: "medium",
            timeStyle: "short",
        });
        const relativeFormatter = new Intl.RelativeTimeFormat(language, { numeric: "auto" });

        const toRelative = (date) => {
            const now = Date.now();
            const seconds = Math.round((date.getTime() - now) / 1000);
            const abs = Math.abs(seconds);

            if (abs < 60) {
                return relativeFormatter.format(seconds, "second");
            }

            const minutes = Math.round(seconds / 60);
            if (Math.abs(minutes) < 60) {
                return relativeFormatter.format(minutes, "minute");
            }

            const hours = Math.round(minutes / 60);
            if (Math.abs(hours) < 24) {
                return relativeFormatter.format(hours, "hour");
            }

            const days = Math.round(hours / 24);
            return relativeFormatter.format(days, "day");
        };

        document.querySelectorAll("time.js-time").forEach((timeNode) => {
            const raw = timeNode.getAttribute("datetime");
            if (!raw) {
                return;
            }

            const date = new Date(raw);
            if (Number.isNaN(date.getTime())) {
                return;
            }

            timeNode.title = absoluteFormatter.format(date);
            timeNode.textContent = toRelative(date);
        });
    };

    const initializeBoardCreation = () => {
        const createButton = document.querySelector("[data-create-board]");
        if (!createButton) {
            return;
        }

        createButton.addEventListener("click", () => {
            openEditorModal({
                title: messages.boardCreateTitle || "Create board",
                description: messages.boardCreateDescription || "",
                primaryLabel: messages.boardCreatePromptName || "Board name",
                secondaryLabel: messages.boardCreatePromptDescription || "Board description (optional)",
                submitLabel: messages.commonCreate || "Create",
                primaryMaxLength: 80,
                secondaryMaxLength: 220,
                trigger: createButton,
                onSubmit: async ({ primary, secondary, setError }) => {
                    try {
                        const result = await postJson("/api/boards/create", {
                            name: primary,
                            description: secondary,
                        });

                        if (result.slug) {
                            window.location.href = `/boards/${encodeURIComponent(result.slug)}`;
                            return false;
                        }

                        window.location.reload();
                        return false;
                    } catch (_error) {
                        setError(messages.boardCreateError || "Could not create board right now.");
                        return false;
                    }
                },
            });
        });
    };

    const initializeBoardInteractions = () => {
        const laneContainer = document.getElementById("board-lanes");
        if (!laneContainer) {
            return;
        }
        const boardSlug = laneContainer.getAttribute("data-board-slug");
        if (!boardSlug) {
            return;
        }

        const announce = (text) => {
            const live = document.getElementById("board-live");
            if (live) {
                live.textContent = text;
            }
        };

        const laneCountLabel = (count) => `${count} cards`;

        const updateLaneCounts = (...lanes) => {
            lanes.forEach((lane) => {
                if (!lane) {
                    return;
                }
                const countNode = lane.querySelector(".lane-count");
                const list = lane.querySelector(".card-list");
                if (!countNode || !list) {
                    return;
                }
                const nextCount = list.children.length;
                countNode.textContent = String(nextCount);
                countNode.setAttribute("aria-label", laneCountLabel(nextCount));
            });
        };

        const createCardElement = (cardData) => {
            const cardId = String(cardData.id || `card-${Date.now()}`);
            const title = String(cardData.title || "Card");
            const meta = String(cardData.meta || "No details");
            const status = String(cardData.status || "New");
            const menuId = `card-menu-${cardId}`;

            const cardItem = document.createElement("li");
            cardItem.className = "card-item";
            cardItem.setAttribute("data-card-id", cardId);

            const card = document.createElement("article");
            card.className = "card";
            card.tabIndex = 0;
            card.setAttribute("data-card-title", title);

            const cardHead = document.createElement("div");
            cardHead.className = "card-head";

            const heading = document.createElement("h3");
            heading.className = "card-title";
            heading.textContent = title;

            const menuTrigger = document.createElement("button");
            menuTrigger.className = "icon-button card-menu-trigger";
            menuTrigger.type = "button";
            menuTrigger.setAttribute("aria-expanded", "false");
            menuTrigger.setAttribute("aria-haspopup", "menu");
            menuTrigger.setAttribute("aria-controls", menuId);

            const triggerIcon = document.createElement("span");
            triggerIcon.setAttribute("aria-hidden", "true");
            triggerIcon.textContent = "...";

            const triggerLabel = document.createElement("span");
            triggerLabel.className = "sr-only";
            triggerLabel.textContent = messages.boardCardActions || "Card actions";

            menuTrigger.append(triggerIcon, triggerLabel);
            cardHead.append(heading, menuTrigger);

            const metaNode = document.createElement("p");
            metaNode.className = "card-meta";
            metaNode.textContent = meta;

            const statusWrap = document.createElement("p");
            statusWrap.className = "card-status";
            const statusTag = document.createElement("span");
            statusTag.className = "tag";
            statusTag.textContent = `${messages.boardStatusPrefix || "Status"}: ${status}`;
            statusWrap.append(statusTag);

            const menu = document.createElement("div");
            menu.className = "card-menu";
            menu.id = menuId;
            menu.setAttribute("role", "menu");
            menu.hidden = true;

            const createMenuButton = (action, icon, label, confirmMessage) => {
                const button = document.createElement("button");
                button.type = "button";
                button.setAttribute("role", "menuitem");
                button.setAttribute("data-card-action", action);
                if (confirmMessage) {
                    button.setAttribute("data-confirm", confirmMessage);
                }

                const iconNode = document.createElement("span");
                iconNode.setAttribute("aria-hidden", "true");
                iconNode.textContent = icon;

                const labelNode = document.createElement("span");
                labelNode.textContent = label;

                button.append(iconNode, labelNode);
                return button;
            };

            menu.append(
                createMenuButton("left", "<", messages.boardMoveLeft || "Move left"),
                createMenuButton("right", ">", messages.boardMoveRight || "Move right"),
                createMenuButton(
                    "archive",
                    "x",
                    messages.boardArchive || "Archive",
                    messages.boardConfirmArchive || "Archive this card? You can undo right after."
                )
            );

            card.append(cardHead, metaNode, statusWrap, menu);
            cardItem.append(card);
            return cardItem;
        };

        const moveCard = async (cardItem, direction) => {
            const currentLane = cardItem.closest(".lane");
            if (!currentLane) {
                return;
            }
            const cardId = cardItem.getAttribute("data-card-id");
            if (!cardId) {
                return;
            }

            const targetLane =
                direction === "left"
                    ? currentLane.previousElementSibling
                    : currentLane.nextElementSibling;

            if (!targetLane || !targetLane.classList.contains("lane")) {
                return;
            }

            const currentList = currentLane.querySelector(".card-list");
            const targetList = targetLane.querySelector(".card-list");
            if (!currentList || !targetList) {
                return;
            }

            const cardNode = cardItem.querySelector(".card");
            const cardTitle = cardNode?.getAttribute("data-card-title") || cardNode?.querySelector(".card-title")?.textContent || "card";
            const targetLaneTitle = targetLane.querySelector(".lane-title")?.textContent || "lane";

            const nextSibling = cardItem.nextElementSibling;
            const restore = () => {
                if (nextSibling && nextSibling.parentElement === currentList) {
                    currentList.insertBefore(cardItem, nextSibling);
                } else {
                    currentList.append(cardItem);
                }
                updateLaneCounts(currentLane, targetLane);
                announce(messages.boardUndoDone || "Action undone.");
            };

            try {
                await postJson(`/api/boards/${encodeURIComponent(boardSlug)}/cards/move`, {
                    card_id: cardId,
                    direction,
                });
            } catch (_error) {
                announce("Could not move card right now.");
                return;
            }

            targetList.append(cardItem);
            updateLaneCounts(currentLane, targetLane);
            announce(
                (messages.boardMoved || "Moved \"__TITLE__\" to __LANE__.")
                    .replace("__TITLE__", cardTitle)
                    .replace("__LANE__", targetLaneTitle)
            );

            showUndoToast(
                (messages.boardMoved || "Moved \"__TITLE__\" to __LANE__.")
                    .replace("__TITLE__", cardTitle)
                    .replace("__LANE__", targetLaneTitle),
                () => {
                    const undoDirection = direction === "left" ? "right" : "left";
                    postJson(`/api/boards/${encodeURIComponent(boardSlug)}/cards/move`, {
                        card_id: cardId,
                        direction: undoDirection,
                    })
                        .then(() => restore())
                        .catch(() => announce("Could not undo move right now."));
                }
            );

            cardNode?.focus();
        };

        const addCard = (lane, laneIndex, triggerButton) => {
            if (!lane || !Number.isInteger(laneIndex)) {
                return;
            }

            const laneTitle = lane.querySelector(".lane-title")?.textContent?.trim() || "lane";
            openEditorModal({
                title: messages.boardAddTitle || "Add card",
                description: (messages.boardAddToLane || "Add a card to __LANE__.").replace("__LANE__", laneTitle),
                primaryLabel: messages.boardAddPromptTitle || "Card title",
                secondaryLabel: messages.boardAddPromptMeta || "Card details (optional)",
                submitLabel: messages.boardAddTitle || "Add card",
                primaryMaxLength: 120,
                secondaryMaxLength: 160,
                trigger: triggerButton || null,
                onSubmit: async ({ primary, secondary, setError }) => {
                    let created;
                    try {
                        created = await postJson(`/api/boards/${encodeURIComponent(boardSlug)}/cards/create`, {
                            title: primary,
                            meta: secondary,
                            lane_index: laneIndex,
                        });
                    } catch (_error) {
                        setError(messages.boardAddError || "Could not add card right now.");
                        return false;
                    }

                    const cardList = lane.querySelector(".card-list");
                    if (!cardList) {
                        return false;
                    }

                    const cardItem = createCardElement(created.card || {});
                    cardList.append(cardItem);
                    updateLaneCounts(lane);

                    const targetLaneTitle =
                        String(created.lane_name || "").trim() ||
                        lane.querySelector(".lane-title")?.textContent ||
                        "lane";
                    announce(
                        (messages.boardAdded || "Added \"__TITLE__\" to __LANE__.")
                            .replace("__TITLE__", primary)
                            .replace("__LANE__", targetLaneTitle)
                    );

                    window.setTimeout(() => {
                        cardItem.querySelector(".card")?.focus();
                    }, 0);
                    return true;
                },
            });
        };

        const archiveCard = async (cardItem, trigger) => {
            const cardNode = cardItem.querySelector(".card");
            const cardTitle = cardNode?.getAttribute("data-card-title") || cardNode?.querySelector(".card-title")?.textContent || "card";
            const lane = cardItem.closest(".lane");
            const list = lane?.querySelector(".card-list");
            const cardId = cardItem.getAttribute("data-card-id");

            if (!lane || !list || !cardId) {
                return;
            }

            const nextSibling = cardItem.nextElementSibling;

            openConfirmModal(
                trigger.getAttribute("data-confirm") || "Confirm?",
                async () => {
                    try {
                        await postJson(`/api/boards/${encodeURIComponent(boardSlug)}/cards/archive`, {
                            card_id: cardId,
                        });
                    } catch (_error) {
                        announce("Could not archive card right now.");
                        return;
                    }

                    cardItem.remove();
                    updateLaneCounts(lane);
                    announce((messages.boardArchived || "Archived \"__TITLE__\".").replace("__TITLE__", cardTitle));

                    showUndoToast(
                        (messages.boardArchived || "Archived \"__TITLE__\".").replace("__TITLE__", cardTitle),
                        () => {
                            postJson(`/api/boards/${encodeURIComponent(boardSlug)}/cards/restore`, {
                                card_id: cardId,
                            })
                                .then(() => {
                                    if (nextSibling && nextSibling.parentElement === list) {
                                        list.insertBefore(cardItem, nextSibling);
                                    } else {
                                        list.append(cardItem);
                                    }
                                    updateLaneCounts(lane);
                                    announce(messages.boardUndoDone || "Action undone.");
                                })
                                .catch(() => announce("Could not undo archive right now."));
                        }
                    );
                },
                trigger
            );
        };

        const closeAllMenus = (except) => {
            laneContainer.querySelectorAll(".card-menu").forEach((menu) => {
                if (except && menu === except) {
                    return;
                }
                menu.hidden = true;
            });
            laneContainer.querySelectorAll(".card-menu-trigger").forEach((trigger) => {
                const controls = trigger.getAttribute("aria-controls");
                const related = controls ? document.getElementById(controls) : null;
                trigger.setAttribute("aria-expanded", related && !related.hidden ? "true" : "false");
            });
        };

        laneContainer.addEventListener("click", (event) => {
            const trigger = event.target.closest(".card-menu-trigger");
            if (trigger) {
                const controlsId = trigger.getAttribute("aria-controls");
                const menu = controlsId ? document.getElementById(controlsId) : null;
                if (!menu) {
                    return;
                }

                const isHidden = menu.hidden;
                closeAllMenus();
                menu.hidden = !isHidden;
                trigger.setAttribute("aria-expanded", isHidden ? "true" : "false");
                return;
            }

            const actionButton = event.target.closest("[data-card-action]");
            if (actionButton) {
                const cardItem = actionButton.closest(".card-item");
                if (!cardItem) {
                    return;
                }
                const action = actionButton.getAttribute("data-card-action");

                if (action === "left") {
                    void moveCard(cardItem, "left");
                }

                if (action === "right") {
                    void moveCard(cardItem, "right");
                }

                if (action === "archive") {
                    void archiveCard(cardItem, actionButton);
                }

                closeAllMenus();
                return;
            }

            if (!event.target.closest(".card-menu")) {
                closeAllMenus();
            }
        });

        document.addEventListener("click", (event) => {
            const addButton = event.target.closest("[data-add-card]");
            if (!addButton) {
                return;
            }

            let lane = addButton.closest(".lane");
            let laneIndex = Number.parseInt(addButton.getAttribute("data-lane-index") || "", 10);

            if (!lane && Number.isInteger(laneIndex)) {
                lane = laneContainer.querySelector(`.lane[data-lane-index="${laneIndex}"]`);
            }

            if (!lane) {
                lane = laneContainer.querySelector(".lane");
            }

            if (!Number.isInteger(laneIndex)) {
                laneIndex = Number.parseInt(lane?.getAttribute("data-lane-index") || "", 10);
            }

            if (!lane || !Number.isInteger(laneIndex)) {
                return;
            }

            addCard(lane, laneIndex, addButton);
        });

        document.addEventListener("click", (event) => {
            if (!laneContainer.contains(event.target)) {
                closeAllMenus();
            }
        });

        laneContainer.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeAllMenus();
                return;
            }

            const menu = event.target.closest(".card-menu");
            if (!menu) {
                return;
            }

            const options = [...menu.querySelectorAll("button")];
            if (!options.length) {
                return;
            }

            const index = options.indexOf(document.activeElement);
            if (event.key === "ArrowDown") {
                event.preventDefault();
                options[(index + 1 + options.length) % options.length].focus();
            }
            if (event.key === "ArrowUp") {
                event.preventDefault();
                options[(index - 1 + options.length) % options.length].focus();
            }
        });

        laneContainer.addEventListener("keydown", (event) => {
            const focusedCard = event.target.closest(".card");
            if (!focusedCard) {
                return;
            }

            const cardItem = focusedCard.closest(".card-item");
            if (!cardItem) {
                return;
            }

            if (event.altKey && event.key === "ArrowLeft") {
                event.preventDefault();
                void moveCard(cardItem, "left");
            }

            if (event.altKey && event.key === "ArrowRight") {
                event.preventDefault();
                void moveCard(cardItem, "right");
            }
        });
    };

    const initializeGlobalShortcuts = () => {
        document.addEventListener("keydown", (event) => {
            if (isInputLike(event.target)) {
                return;
            }

            if ((event.key === "?" || (event.key === "/" && event.shiftKey)) && !event.metaKey && !event.ctrlKey) {
                event.preventDefault();
                window.location.href = "/help";
            }
        });
    };

    initializePreferences();
    initializeNavToggle();
    initializeFoldables();
    initializeDismissableFlash();
    initializeCharacterCounters();
    initializeSavingAnnouncements();
    initializeConfirmModal();
    initializeEditorModal();
    initializeLocalizedTimes();
    initializeBoardCreation();
    initializeBoardInteractions();
    initializeGlobalShortcuts();
})();
