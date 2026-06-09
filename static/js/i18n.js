/* ForensAI — RU / EN / UZ */
(function () {
  const STORAGE_LANG = "forensai_lang";
  const STORAGE_THEME = "forensai_theme";

  const messages = {
    ru: {
      "app.title": "ForensAI — Цифровая экспертиза",
      "nav.pro": "Pro",
      "nav.referral": "Реферал",
      "nav.history": "История",
      "theme.dark": "Тёмная",
      "theme.light": "Светлая",
      "lang.ru": "Русский",
      "lang.en": "English",
      "lang.uz": "Oʻzbek",
      "status.serverDown": "Сервер недоступен",
      "tab.file": "Файл",
      "tab.text": "Текст",
      "tab.compare": "Сравнение",
      "tab.batch": "Пакет",
      "upload.pickFile": "Выберите файл",
      "upload.hint": "Изображение, видео или документ · до 50 МБ",
      "upload.textPlaceholder": "Вставьте текст для анализа…",
      "upload.fileA": "Файл A",
      "upload.fileB": "Файл B",
      "upload.fileAHint": "Оригинал / эталон",
      "upload.fileBHint": "Подозрительный",
      "upload.batchHint": "Несколько файлов · по очереди",
      "btn.analyze": "Анализировать",
      "empty.title": "Результат появится здесь",
      "empty.text": "Загрузите материал и нажмите «Анализировать».",
      "report.confidence": "Уверенность",
      "report.exportPdf": "PDF",
      "report.exportJson": "JSON",
      "score.ai": "Индекс ИИ",
      "score.plagiarism": "Плагиат",
      "score.authenticity": "Подлинность",
      "section.compare": "Сравнение двух материалов",
      "section.preview": "Превью",
      "section.zones": "Карта зон",
      "section.categories": "Категории риска",
      "section.timeline": "Временная шкала",
      "section.reasoning": "Обоснование",
      "section.osint": "OSINT",
      "section.evidence": "Улики",
      "section.segments": "Фрагменты текста",
      "section.highlight": "Разметка",
      "tag.ok": "Норма",
      "tag.warn": "Риск",
      "tag.bad": "Высокий",
      "tag.ai": "ИИ",
      "tag.pl": "Плагиат",
      "table.num": "#",
      "table.text": "Текст",
      "table.ai": "ИИ",
      "table.plagiarism": "Плагиат",
      "table.flags": "Маркеры",
      "loading.title": "Анализ…",
      "loading.prep": "Подготовка",
      "footer.disclaimer": "Результат носит аналитический характер и не является юридическим заключением.",
      "verdict.ai_generated": "Сгенерировано ИИ",
      "verdict.human_created": "Создано человеком",
      "verdict.hybrid": "Подозрение на ИИ",
      "verdict.compareTitle": "Сравнение двух материалов",
      "verdict.match": "Вердикты совпадают",
      "verdict.deltaAi": "Δ AI {n}",
      "mode.gemini": "Gemini + Forensics",
      "mode.openai": "OpenAI + Forensics",
      "mode.heuristics": "Эвристики",
      "mode.local": "Локальный анализ",
      "mode.fallback": "Резервный режим",
      "mode.compare": "Режим сравнения",
      "error.pickFile": "Выберите файл",
      "error.enterText": "Введите текст",
      "error.pickBoth": "Выберите оба файла",
      "error.network": "Сеть недоступна",
      "error.server": "Некорректный ответ сервера",
      "error.analyze": "Ошибка анализа",
      "error.limit": "Лимит бесплатных анализов исчерпан. Оформите Pro или пригласите друга.",
      "error.auth": "Войдите в аккаунт, чтобы продолжить",
      "error.runFirst": "Сначала проведите анализ",
      "error.popup": "Разрешите всплывающие окна для PDF",
      "reasoning.summary": "Резюме",
      "reasoning.ai": "Анализ ИИ",
      "reasoning.plagiarism": "Плагиат / монтаж",
      "reasoning.conclusion": "Заключение",
      "reasoning.unavailable": "Обоснование недоступно",
      "reasoning.pending": "Обоснование формируется…",
      "evidence.none": "Явных аномалий не обнаружено",
      "risk.clean": "Норма",
      "risk.low": "Низкий",
      "risk.medium": "Средний",
      "risk.high": "Высокий",
      "cat.anatomy": "Анатомия",
      "cat.lighting": "Свет",
      "cat.geometry": "Геометрия",
      "cat.artifacts": "Артефакты",
      "cat.metadata": "Метаданные",
      "cat.biometrics": "Биометрия",
      "cat.sync": "Синхрон",
      "metric.crit": "Крит.",
      "metric.mod": "Умер.",
      "metric.total": "Всего улик",
      "metric.zones": "Зон",
      "metric.quality": "Качество",
      "metric.frames": "Кадры",
      "sub.title": "Подписка ForensAI Pro",
      "sub.free": "Бесплатно",
      "sub.pro": "Pro",
      "sub.perMonth": "/ мес",
      "sub.analyses": "Анализов в месяц",
      "sub.unlimited": "Безлимит",
      "sub.current": "Текущий план",
      "sub.upgrade": "Оформить Pro",
      "sub.active": "Pro активен",
      "sub.demoPay": "Демо-оплата (без карты)",
      "sub.remaining": "Осталось анализов: {n}",
      "sub.discount": "Ваша скидка: {n}%",
      "ref.title": "Реферальная программа",
      "ref.desc": "Пригласите реального пользователя: после его первого анализа вы получите +{n}% скидку на Pro (до 50%) и +2 бонусных анализа. Друг получает {n}% скидку.",
      "ref.yourCode": "Ваш код",
      "ref.link": "Ссылка для друга",
      "ref.apply": "У меня есть код друга",
      "ref.applyBtn": "Применить",
      "ref.verified": "Подтверждённых приглашений: {n}",
      "ref.copied": "Скопировано",
      "hist.title": "История отчётов",
      "hist.empty": "Пока нет сохранённых отчётов",
      "hist.open": "Открыть",
      "hist.clear": "Очистить",
      "quota.badge": "{plan} · {left} ост.",
      "auth.title": "Вход в ForensAI",
      "auth.subtitle": "Войдите, чтобы сохранять квоту, историю и рефералы",
      "auth.signIn": "Вход",
      "auth.signUp": "Регистрация",
      "auth.login": "Войти",
      "auth.logout": "Выйти",
      "auth.email": "Email",
      "auth.password": "Пароль",
      "auth.google": "Войти через Google",
      "auth.or": "или",
      "auth.fillFields": "Заполните email и пароль",
      "auth.checkEmail": "Проверьте почту для подтверждения регистрации",
      "auth.user": "Пользователь",
      "auth.signInToAnalyze": "Войдите для анализа",
      "batch.queue": "В очереди: {n}",
      "batch.done": "Готово {done}/{total}",
      "osint.noData": "Нет дополнительных данных",
      "upload.filesSelected": "Выбрано: {n}",
      "zones.allOk": "Все зоны в пределах нормы",
      "zone.unknown": "Зона",
      "zone.riskLabel": "Риск: {risk}",
      "zone.sec": "{n}с",
      "zone.noise": "Шум",
      "zone.sharp": "Резк.",
      "zone.tl": "верх-лево",
      "zone.tc": "верх-центр",
      "zone.tr": "верх-право",
      "zone.ml": "центр-лево",
      "zone.mc": "центр",
      "zone.mr": "центр-право",
      "zone.bl": "низ-лево",
      "zone.bc": "низ-центр",
      "zone.br": "низ-право",
      "severity.critical": "критический",
      "severity.moderate": "умеренный",
      "severity.minor": "незначительный",
      "severity.clean": "норма",
      "report.risk.high": "высокий",
      "report.risk.moderate": "умеренный",
      "report.risk.low": "низкий",
      "report.riskLevel.high": "высокий",
      "report.riskLevel.moderate": "умеренный",
      "report.riskLevel.low": "низкий",
      "report.summary.line1": "Вердикт: {verdict}. AI-индекс {ai}/100 ({risk} риск) · подлинность {auth}/100 · плагиат {pl}/100 · уверенность {conf}%.",
      "report.summary.line2": "Улики: {critical} критических, {moderate} умеренных.",
      "report.summary.sentences": "Проанализировано {n} предложений.",
      "report.summary.image": "Изображение {res} ({mp} MP), зон проверено: {zones}.",
      "report.summary.imageCat": "Макс. риск — категория «{cat}»: {val}/100.",
      "report.summary.video": "Видео {dur}с · {fps} fps · кадров: {frames} · зон: {zones}.",
      "report.summary.videoBio": "Биометрия: {bio}/100 · Синхрон: {sync}/100.",
      "report.summary.engine": "Движок: {mode}.",
      "report.ai.open": "Индекс ИИ {ai}/100 ({level}).",
      "report.ai.cats": "Категории: {cats}.",
      "report.ai.zones": "Проблемные зоны: {zones}.",
      "report.ai.flags": "Флагов в тексте: {n} из {total}.",
      "report.ai.critical": "Критических улик: {n}.",
      "report.pl.image": "Индекс заимствования/монтажа: {pl}/100. ELA variance: {ela}, EXIF: {exif}.",
      "report.pl.video": "Индекс монтажа/deepfake: {pl}/100. Variance кадров: {var}, аудио: {audio}.",
      "report.pl.low": "Плагиат {pl}/100 — внутренних дубликатов не обнаружено.",
      "report.pl.flagged": "Плагиат {pl}/100 — подозрительных предложений: {n}.",
      "report.conclusion": "Вердикт: {verdict} · уверенность {conf}% · AI {ai} · плагиат {pl} · authenticity {auth}.",
      "report.exif.yes": "есть",
      "report.exif.no": "отсутствует",
      "report.audio.yes": "да",
      "report.audio.no": "нет",
      "compare.line": "«{name}»: {verdict} (AI {ai}, подлинность {auth})",
      "compare.match": "Вердикты совпадают.",
      "compare.differ": "Вердикты различаются — материалы относятся к разным классам риска.",
      "compare.delta": "Разница AI-индекса: {ai} п.п. · плагиат: {pl} п.п.",
      "compare.gapHigh": "Существенный разрыв: выше риск у «{riskier}», ниже у «{safer}».",
      "compare.gapModerate": "Умеренное расхождение — стоит сопоставить улики по каждому файлу.",
      "score.short.ai": "AI",
      "score.short.pl": "PL",
      "score.short.auth": "AUTH",
      "score.short.conf": "CONF",
      "osint.rec.img1": "Сверьте хеш файла с оригиналом источника, если он известен.",
      "osint.rec.img2": "Проверьте дату первой публикации через обратный поиск.",
      "osint.rec.img3": "Сопоставите EXIF с заявленным устройством и местом съёмки.",
      "osint.rec.vid1": "Извлеките ключевые кадры и проверьте их отдельно как изображения.",
      "osint.rec.vid2": "Сравните синхронизацию губ и мигание при подозрении на deepfake.",
      "osint.rec.txt1": "Проверьте уникальные фрагменты в поисковике в кавычках.",
      "osint.rec.txt2": "Сопоставьте стиль с другими публикациями автора.",
      "osint.rec.empty": "Загрузите файл для расширенного OSINT-анализа.",
      "osint.exifMissing": "EXIF: отсутствует",
      "osint.exifError": "EXIF: ошибка чтения",
      "osint.resolution": "Разрешение: {w}×{h} ({mp} MP)",
      "osint.camera": "Камера (EXIF): {model}",
      "osint.noExifHint": "EXIF отсутствует — возможна пересылка или экспорт из генератора",
      "osint.format": "Формат: {fmt}",
      "osint.duration": "Длительность: {dur} с",
      "osint.fps": "FPS: {fps}",
      "osint.audio": "Аудио: {val}",
      "ev.zone": "Зона: {region}",
      "ev.plagiarism": "Плагиат: {cat}",
      "evCat.generator": "ПО генератора",
      "evCat.cameraMeta": "Метаданные камеры",
      "evCat.metadata": "Метаданные",
      "evCat.geometry": "Геометрия",
      "evCat.artifacts": "Артефакты",
      "evCat.visualSynth": "Визуальная синтетика",
      "evCat.videoMeta": "Метаданные видео",
      "evCat.audioTrack": "Аудиодорожка",
      "evCat.frames": "Кадры",
      "evCat.frameStability": "Стабильность кадров",
      "evCat.ela": "ELA",
    },
    en: {
      "app.title": "ForensAI — Digital Forensics",
      "nav.pro": "Pro",
      "nav.referral": "Referral",
      "nav.history": "History",
      "theme.dark": "Dark",
      "theme.light": "Light",
      "lang.ru": "Русский",
      "lang.en": "English",
      "lang.uz": "Oʻzbek",
      "status.serverDown": "Server unavailable",
      "tab.file": "File",
      "tab.text": "Text",
      "tab.compare": "Compare",
      "tab.batch": "Batch",
      "upload.pickFile": "Choose a file",
      "upload.hint": "Image, video or document · up to 50 MB",
      "upload.textPlaceholder": "Paste text for analysis…",
      "upload.fileA": "File A",
      "upload.fileB": "File B",
      "upload.fileAHint": "Original / reference",
      "upload.fileBHint": "Suspect",
      "upload.batchHint": "Multiple files · one by one",
      "btn.analyze": "Analyze",
      "empty.title": "Results will appear here",
      "empty.text": "Upload material and click Analyze.",
      "report.confidence": "Confidence",
      "report.exportPdf": "PDF",
      "report.exportJson": "JSON",
      "score.ai": "AI index",
      "score.plagiarism": "Plagiarism",
      "score.authenticity": "Authenticity",
      "section.compare": "Two-material comparison",
      "section.preview": "Preview",
      "section.zones": "Zone map",
      "section.categories": "Risk categories",
      "section.timeline": "Timeline",
      "section.reasoning": "Reasoning",
      "section.osint": "OSINT",
      "section.evidence": "Evidence",
      "section.segments": "Text segments",
      "section.highlight": "Markup",
      "tag.ok": "OK",
      "tag.warn": "Risk",
      "tag.bad": "High",
      "tag.ai": "AI",
      "tag.pl": "Plagiarism",
      "table.num": "#",
      "table.text": "Text",
      "table.ai": "AI",
      "table.plagiarism": "Plagiarism",
      "table.flags": "Flags",
      "loading.title": "Analyzing…",
      "loading.prep": "Preparing",
      "footer.disclaimer": "Results are analytical only and not legal conclusions.",
      "verdict.ai_generated": "AI generated",
      "verdict.human_created": "Human created",
      "verdict.hybrid": "AI suspicion",
      "verdict.compareTitle": "Two-material comparison",
      "verdict.match": "Verdicts match",
      "verdict.deltaAi": "Δ AI {n}",
      "mode.gemini": "Gemini + Forensics",
      "mode.openai": "OpenAI + Forensics",
      "mode.heuristics": "Heuristics",
      "mode.local": "Local forensics",
      "mode.fallback": "Fallback mode",
      "mode.compare": "Compare mode",
      "error.pickFile": "Choose a file",
      "error.enterText": "Enter text",
      "error.pickBoth": "Choose both files",
      "error.network": "Network unavailable",
      "error.server": "Invalid server response",
      "error.analyze": "Analysis error",
      "error.limit": "Free analysis limit reached. Upgrade to Pro or invite a friend.",
      "error.auth": "Sign in to continue",
      "error.runFirst": "Run an analysis first",
      "error.popup": "Allow pop-ups for PDF export",
      "reasoning.summary": "Summary",
      "reasoning.ai": "AI analysis",
      "reasoning.plagiarism": "Plagiarism / edit",
      "reasoning.conclusion": "Conclusion",
      "reasoning.unavailable": "Reasoning unavailable",
      "reasoning.pending": "Building reasoning…",
      "evidence.none": "No significant anomalies",
      "risk.clean": "Clean",
      "risk.low": "Low",
      "risk.medium": "Medium",
      "risk.high": "High",
      "cat.anatomy": "Anatomy",
      "cat.lighting": "Lighting",
      "cat.geometry": "Geometry",
      "cat.artifacts": "Artifacts",
      "cat.metadata": "Metadata",
      "cat.biometrics": "Biometrics",
      "cat.sync": "Sync",
      "metric.crit": "Crit.",
      "metric.mod": "Mod.",
      "metric.total": "Total evidence",
      "metric.zones": "Zones",
      "metric.quality": "Quality",
      "metric.frames": "Frames",
      "sub.title": "ForensAI Pro subscription",
      "sub.free": "Free",
      "sub.pro": "Pro",
      "sub.perMonth": "/ mo",
      "sub.analyses": "Analyses per month",
      "sub.unlimited": "Unlimited",
      "sub.current": "Current plan",
      "sub.upgrade": "Get Pro",
      "sub.active": "Pro active",
      "sub.demoPay": "Demo payment (no card)",
      "sub.remaining": "Analyses left: {n}",
      "sub.discount": "Your discount: {n}%",
      "ref.title": "Referral program",
      "ref.desc": "Invite a real user: after their first analysis you get +{n}% off Pro (up to 50%) and +2 bonus analyses. They get {n}% off.",
      "ref.yourCode": "Your code",
      "ref.link": "Invite link",
      "ref.apply": "I have a friend's code",
      "ref.applyBtn": "Apply",
      "ref.verified": "Verified invites: {n}",
      "ref.copied": "Copied",
      "hist.title": "Report history",
      "hist.empty": "No saved reports yet",
      "hist.open": "Open",
      "hist.clear": "Clear",
      "quota.badge": "{plan} · {left} left",
      "auth.title": "Sign in to ForensAI",
      "auth.subtitle": "Sign in to keep your quota, history, and referrals",
      "auth.signIn": "Sign in",
      "auth.signUp": "Sign up",
      "auth.login": "Sign in",
      "auth.logout": "Sign out",
      "auth.email": "Email",
      "auth.password": "Password",
      "auth.google": "Continue with Google",
      "auth.or": "or",
      "auth.fillFields": "Enter email and password",
      "auth.checkEmail": "Check your email to confirm sign-up",
      "auth.user": "User",
      "auth.signInToAnalyze": "Sign in to analyze",
      "batch.queue": "Queued: {n}",
      "batch.done": "Done {done}/{total}",
      "osint.noData": "No additional data",
      "upload.filesSelected": "Selected: {n}",
      "zones.allOk": "All zones within normal range",
      "zone.unknown": "Zone",
      "zone.riskLabel": "Risk: {risk}",
      "zone.sec": "{n}s",
      "zone.noise": "Noise",
      "zone.sharp": "Sharp.",
      "zone.tl": "top-left",
      "zone.tc": "top-center",
      "zone.tr": "top-right",
      "zone.ml": "center-left",
      "zone.mc": "center",
      "zone.mr": "center-right",
      "zone.bl": "bottom-left",
      "zone.bc": "bottom-center",
      "zone.br": "bottom-right",
      "severity.critical": "critical",
      "severity.moderate": "moderate",
      "severity.minor": "minor",
      "severity.clean": "clean",
      "report.risk.high": "high",
      "report.risk.moderate": "moderate",
      "report.risk.low": "low",
      "report.riskLevel.high": "high",
      "report.riskLevel.moderate": "moderate",
      "report.riskLevel.low": "low",
      "report.summary.line1": "Verdict: {verdict}. AI index {ai}/100 ({risk} risk) · authenticity {auth}/100 · plagiarism {pl}/100 · confidence {conf}%.",
      "report.summary.line2": "Evidence: {critical} critical, {moderate} moderate.",
      "report.summary.sentences": "Analyzed {n} sentences.",
      "report.summary.image": "Image {res} ({mp} MP), zones checked: {zones}.",
      "report.summary.imageCat": "Peak risk — category «{cat}»: {val}/100.",
      "report.summary.video": "Video {dur}s · {fps} fps · frames: {frames} · zones: {zones}.",
      "report.summary.videoBio": "Biometrics: {bio}/100 · Sync: {sync}/100.",
      "report.summary.engine": "Engine: {mode}.",
      "report.ai.open": "AI index {ai}/100 ({level}).",
      "report.ai.cats": "Categories: {cats}.",
      "report.ai.zones": "Hot zones: {zones}.",
      "report.ai.flags": "Text flags: {n} of {total}.",
      "report.ai.critical": "Critical evidence items: {n}.",
      "report.pl.image": "Borrowing/edit index: {pl}/100. ELA variance: {ela}, EXIF: {exif}.",
      "report.pl.video": "Edit/deepfake index: {pl}/100. Frame variance: {var}, audio: {audio}.",
      "report.pl.low": "Plagiarism {pl}/100 — no internal duplicates detected.",
      "report.pl.flagged": "Plagiarism {pl}/100 — suspicious sentences: {n}.",
      "report.conclusion": "Verdict: {verdict} · confidence {conf}% · AI {ai} · plagiarism {pl} · authenticity {auth}.",
      "report.exif.yes": "present",
      "report.exif.no": "missing",
      "report.audio.yes": "yes",
      "report.audio.no": "no",
      "compare.line": "«{name}»: {verdict} (AI {ai}, authenticity {auth})",
      "compare.match": "Verdicts match.",
      "compare.differ": "Verdicts differ — materials fall into different risk classes.",
      "compare.delta": "AI index gap: {ai} pp · plagiarism: {pl} pp.",
      "compare.gapHigh": "Large gap: higher risk at «{riskier}», lower at «{safer}».",
      "compare.gapModerate": "Moderate gap — compare evidence for each file.",
      "score.short.ai": "AI",
      "score.short.pl": "PL",
      "score.short.auth": "AUTH",
      "score.short.conf": "CONF",
      "osint.rec.img1": "Compare the file hash with the source original if known.",
      "osint.rec.img2": "Check first publication date via reverse image search.",
      "osint.rec.img3": "Match EXIF with the claimed device and shooting location.",
      "osint.rec.vid1": "Extract key frames and analyze them as separate images.",
      "osint.rec.vid2": "Check lip sync and blinking if deepfake is suspected.",
      "osint.rec.txt1": "Search unique quoted fragments in a search engine.",
      "osint.rec.txt2": "Compare writing style with the author's other posts.",
      "osint.rec.empty": "Upload a file for extended OSINT analysis.",
      "osint.exifMissing": "EXIF: none",
      "osint.exifError": "EXIF: read error",
      "osint.resolution": "Resolution: {w}×{h} ({mp} MP)",
      "osint.camera": "Camera (EXIF): {model}",
      "osint.noExifHint": "No EXIF — possible reshare or export from a generator",
      "osint.format": "Format: {fmt}",
      "osint.duration": "Duration: {dur} s",
      "osint.fps": "FPS: {fps}",
      "osint.audio": "Audio: {val}",
      "ev.zone": "Zone: {region}",
      "ev.plagiarism": "Plagiarism: {cat}",
      "evCat.generator": "Generator software",
      "evCat.cameraMeta": "Camera metadata",
      "evCat.metadata": "Metadata",
      "evCat.geometry": "Geometry",
      "evCat.artifacts": "Artifacts",
      "evCat.visualSynth": "Visual synthesis",
      "evCat.videoMeta": "Video metadata",
      "evCat.audioTrack": "Audio track",
      "evCat.frames": "Frames",
      "evCat.frameStability": "Frame stability",
      "evCat.ela": "ELA",
    },
    uz: {
      "app.title": "ForensAI — Raqamli ekspertiza",
      "nav.pro": "Pro",
      "nav.referral": "Referal",
      "nav.history": "Tarix",
      "theme.dark": "Qorongʻu",
      "theme.light": "Yorugʻ",
      "lang.ru": "Русский",
      "lang.en": "English",
      "lang.uz": "Oʻzbek",
      "status.serverDown": "Server ishlamayapti",
      "tab.file": "Fayl",
      "tab.text": "Matn",
      "tab.compare": "Taqqoslash",
      "tab.batch": "Paket",
      "upload.pickFile": "Fayl tanlang",
      "upload.hint": "Rasm, video yoki hujjat · 50 MB gacha",
      "upload.textPlaceholder": "Tahlil uchun matn kiriting…",
      "upload.fileA": "Fayl A",
      "upload.fileB": "Fayl B",
      "upload.fileAHint": "Asl / etalon",
      "upload.fileBHint": "Shubhali",
      "upload.batchHint": "Bir nechta fayl · ketma-ket",
      "btn.analyze": "Tahlil qilish",
      "empty.title": "Natija shu yerda chiqadi",
      "empty.text": "Material yuklang va «Tahlil qilish» ni bosing.",
      "report.confidence": "Ishonch",
      "report.exportPdf": "PDF",
      "report.exportJson": "JSON",
      "score.ai": "AI indeksi",
      "score.plagiarism": "Plagiat",
      "score.authenticity": "Haqiqiylik",
      "section.compare": "Ikki material taqqoslash",
      "section.preview": "Ko‘rib chiqish",
      "section.zones": "Zonalar xaritasi",
      "section.categories": "Xavf toifalari",
      "section.timeline": "Vaqt chizig‘i",
      "section.reasoning": "Asoslash",
      "section.osint": "OSINT",
      "section.evidence": "Dalillar",
      "section.segments": "Matn parchalari",
      "section.highlight": "Belgilash",
      "tag.ok": "Norma",
      "tag.warn": "Xavf",
      "tag.bad": "Yuqori",
      "tag.ai": "AI",
      "tag.pl": "Plagiat",
      "table.num": "#",
      "table.text": "Matn",
      "table.ai": "AI",
      "table.plagiarism": "Plagiat",
      "table.flags": "Belgilar",
      "loading.title": "Tahlil…",
      "loading.prep": "Tayyorgarlik",
      "footer.disclaimer": "Natija faqat tahliliy; huquqiy xulosa emas.",
      "verdict.ai_generated": "AI yaratgan",
      "verdict.human_created": "Inson yaratgan",
      "verdict.hybrid": "AI shubhasi",
      "verdict.compareTitle": "Ikki material taqqoslash",
      "verdict.match": "Xulosalar mos",
      "verdict.deltaAi": "Δ AI {n}",
      "mode.gemini": "Gemini + Forensics",
      "mode.openai": "OpenAI + Forensics",
      "mode.heuristics": "Evristika",
      "mode.local": "Mahalliy tahlil",
      "mode.fallback": "Zaxira rejim",
      "mode.compare": "Taqqoslash rejimi",
      "error.pickFile": "Fayl tanlang",
      "error.enterText": "Matn kiriting",
      "error.pickBoth": "Ikkala faylni tanlang",
      "error.network": "Tarmoq yo‘q",
      "error.server": "Server javobi noto‘g‘ri",
      "error.analyze": "Tahlil xatosi",
      "error.limit": "Bepul limit tugadi. Pro yoki do‘stni taklif qiling.",
      "error.auth": "Davom etish uchun tizimga kiring",
      "error.runFirst": "Avval tahlil qiling",
      "error.popup": "PDF uchun pop-up ruxsat bering",
      "reasoning.summary": "Xulosa",
      "reasoning.ai": "AI tahlili",
      "reasoning.plagiarism": "Plagiat / montaj",
      "reasoning.conclusion": "Yakun",
      "reasoning.unavailable": "Asoslash mavjud emas",
      "reasoning.pending": "Asoslash tayyorlanmoqda…",
      "evidence.none": "Anomaliyalar topilmadi",
      "risk.clean": "Norma",
      "risk.low": "Past",
      "risk.medium": "O‘rta",
      "risk.high": "Yuqori",
      "cat.anatomy": "Anatomiya",
      "cat.lighting": "Yorug‘lik",
      "cat.geometry": "Geometriya",
      "cat.artifacts": "Artefaktlar",
      "cat.metadata": "Metadata",
      "cat.biometrics": "Biometriya",
      "cat.sync": "Sinxron",
      "metric.crit": "Krit.",
      "metric.mod": "O‘rt.",
      "metric.total": "Jami dalil",
      "metric.zones": "Zonalar",
      "metric.quality": "Sifat",
      "metric.frames": "Kadrlar",
      "sub.title": "ForensAI Pro obuna",
      "sub.free": "Bepul",
      "sub.pro": "Pro",
      "sub.perMonth": "/ oy",
      "sub.analyses": "Oylik tahlillar",
      "sub.unlimited": "Cheksiz",
      "sub.current": "Joriy reja",
      "sub.upgrade": "Pro olish",
      "sub.active": "Pro faol",
      "sub.demoPay": "Demo to‘lov (karta yo‘q)",
      "sub.remaining": "Qolgan tahlillar: {n}",
      "sub.discount": "Chegirma: {n}%",
      "ref.title": "Referal dasturi",
      "ref.desc": "Haqiqiy foydalanuvchini taklif qiling: uning birinchi tahlilidan keyin siz Pro ga +{n}% chegirma (50% gacha) va +2 bonus tahlil olasiz. Do‘st {n}% chegirma oladi.",
      "ref.yourCode": "Sizning kodingiz",
      "ref.link": "Taklif havolasi",
      "ref.apply": "Do‘st kodi bor",
      "ref.applyBtn": "Qo‘llash",
      "ref.verified": "Tasdiqlangan takliflar: {n}",
      "ref.copied": "Nusxa olindi",
      "hist.title": "Hisobotlar tarixi",
      "hist.empty": "Saqlangan hisobot yo‘q",
      "hist.open": "Ochish",
      "hist.clear": "Tozalash",
      "quota.badge": "{plan} · {left} qoldi",
      "auth.title": "ForensAI ga kirish",
      "auth.subtitle": "Kvota, tarix va referallarni saqlash uchun kiring",
      "auth.signIn": "Kirish",
      "auth.signUp": "Ro‘yxatdan o‘tish",
      "auth.login": "Kirish",
      "auth.logout": "Chiqish",
      "auth.email": "Email",
      "auth.password": "Parol",
      "auth.google": "Google orqali kirish",
      "auth.or": "yoki",
      "auth.fillFields": "Email va parolni kiriting",
      "auth.checkEmail": "Ro‘yxatdan o‘tishni tasdiqlash uchun pochtani tekshiring",
      "auth.user": "Foydalanuvchi",
      "auth.signInToAnalyze": "Tahlil uchun kiring",
      "batch.queue": "Navbat: {n}",
      "batch.done": "Tayyor {done}/{total}",
      "osint.noData": "Qo‘shimcha ma’lumot yo‘q",
      "upload.filesSelected": "Tanlandi: {n}",
      "zones.allOk": "Barcha zonalar me’yorda",
      "zone.unknown": "Zona",
      "zone.riskLabel": "Xavf: {risk}",
      "zone.sec": "{n}s",
      "zone.noise": "Shovqin",
      "zone.sharp": "Keskin.",
      "zone.tl": "yuqori-chap",
      "zone.tc": "yuqori-markaz",
      "zone.tr": "yuqori-o‘ng",
      "zone.ml": "markaz-chap",
      "zone.mc": "markaz",
      "zone.mr": "markaz-o‘ng",
      "zone.bl": "past-chap",
      "zone.bc": "past-markaz",
      "zone.br": "past-o‘ng",
      "severity.critical": "kritik",
      "severity.moderate": "o‘rtacha",
      "severity.minor": "kichik",
      "severity.clean": "me’yor",
      "report.risk.high": "yuqori",
      "report.risk.moderate": "o‘rtacha",
      "report.risk.low": "past",
      "report.riskLevel.high": "yuqori",
      "report.riskLevel.moderate": "o‘rtacha",
      "report.riskLevel.low": "past",
      "report.summary.line1": "Xulosa: {verdict}. AI indeksi {ai}/100 ({risk} xavf) · haqiqiylik {auth}/100 · plagiat {pl}/100 · ishonch {conf}%.",
      "report.summary.line2": "Dalillar: {critical} kritik, {moderate} o‘rtacha.",
      "report.summary.sentences": "{n} ta gap tahlil qilindi.",
      "report.summary.image": "Rasm {res} ({mp} MP), tekshirilgan zonalar: {zones}.",
      "report.summary.imageCat": "Maks. xavf — «{cat}» toifasi: {val}/100.",
      "report.summary.video": "Video {dur}s · {fps} fps · kadrlar: {frames} · zonalar: {zones}.",
      "report.summary.videoBio": "Biometriya: {bio}/100 · Sinxron: {sync}/100.",
      "report.summary.engine": "Dvigatel: {mode}.",
      "report.ai.open": "AI indeksi {ai}/100 ({level}).",
      "report.ai.cats": "Toifalar: {cats}.",
      "report.ai.zones": "Muammoli zonalar: {zones}.",
      "report.ai.flags": "Matnda belgilar: {n} / {total}.",
      "report.ai.critical": "Kritik dalillar: {n}.",
      "report.pl.image": "O‘zlashtirish/montaj indeksi: {pl}/100. ELA: {ela}, EXIF: {exif}.",
      "report.pl.video": "Montaj/deepfake indeksi: {pl}/100. Kadr dispersiyasi: {var}, audio: {audio}.",
      "report.pl.low": "Plagiat {pl}/100 — ichki dublikatlar topilmadi.",
      "report.pl.flagged": "Plagiat {pl}/100 — shubhali gaplar: {n}.",
      "report.conclusion": "Xulosa: {verdict} · ishonch {conf}% · AI {ai} · plagiat {pl} · haqiqiylik {auth}.",
      "report.exif.yes": "bor",
      "report.exif.no": "yo‘q",
      "report.audio.yes": "ha",
      "report.audio.no": "yo‘q",
      "compare.line": "«{name}»: {verdict} (AI {ai}, haqiqiylik {auth})",
      "compare.match": "Xulosalar mos keladi.",
      "compare.differ": "Xulosalar farq qiladi — materiallar turli xavf sinflarida.",
      "compare.delta": "AI indeksi farqi: {ai} b.p. · plagiat: {pl} b.p.",
      "compare.gapHigh": "Katta farq: yuqori xavf «{riskier}», past «{safer}».",
      "compare.gapModerate": "O‘rtacha farq — har bir fayl bo‘yicha dalillarni solishtiring.",
      "score.short.ai": "AI",
      "score.short.pl": "PL",
      "score.short.auth": "AUTH",
      "score.short.conf": "CONF",
      "osint.rec.img1": "Fayl xeshini manba originali bilan solishtiring.",
      "osint.rec.img2": "Teskari qidiruv orqali birinchi nashr sanasini tekshiring.",
      "osint.rec.img3": "EXIFni e’lon qilingan qurilma va joy bilan solishtiring.",
      "osint.rec.vid1": "Asosiy kadrlarni ajrating va alohida rasm sifatida tahlil qiling.",
      "osint.rec.vid2": "Deepfake shubhasida lab sinxroni va miltillashni tekshiring.",
      "osint.rec.txt1": "Noyob parchalarni qidiruvda qo‘shtirnoqda qidiring.",
      "osint.rec.txt2": "Uslubni muallifning boshqa postlari bilan solishtiring.",
      "osint.rec.empty": "Kengaytirilgan OSINT uchun fayl yuklang.",
      "osint.exifMissing": "EXIF: yo‘q",
      "osint.exifError": "EXIF: o‘qish xatosi",
      "osint.resolution": "O‘lcham: {w}×{h} ({mp} MP)",
      "osint.camera": "Kamera (EXIF): {model}",
      "osint.noExifHint": "EXIF yo‘q — qayta yuborish yoki generator eksporti mumkin",
      "osint.format": "Format: {fmt}",
      "osint.duration": "Davomiylik: {dur} s",
      "osint.fps": "FPS: {fps}",
      "osint.audio": "Audio: {val}",
      "ev.zone": "Zona: {region}",
      "ev.plagiarism": "Plagiat: {cat}",
      "evCat.generator": "Generator dasturi",
      "evCat.cameraMeta": "Kamera metama’lumoti",
      "evCat.metadata": "Metama’lumot",
      "evCat.geometry": "Geometriya",
      "evCat.artifacts": "Artefaktlar",
      "evCat.visualSynth": "Vizual sintetika",
      "evCat.videoMeta": "Video metama’lumoti",
      "evCat.audioTrack": "Audio yo‘l",
      "evCat.frames": "Kadrlar",
      "evCat.frameStability": "Kadr barqarorligi",
      "evCat.ela": "ELA",
    },
  };

  let lang = localStorage.getItem(STORAGE_LANG) || "ru";
  if (!messages[lang]) lang = "ru";

  function t(key, vars = {}) {
    let s = messages[lang][key] || messages.ru[key] || key;
    Object.entries(vars).forEach(([k, v]) => {
      s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    });
    return s;
  }

  function verdictLabel(verdict, fallback) {
    const k = `verdict.${verdict}`;
    return messages[lang][k] ? t(k) : (fallback || verdict);
  }

  function categoryLabel(key) {
    return t(`cat.${key}`) !== `cat.${key}` ? t(`cat.${key}`) : key;
  }

  const REGION_MAP = {
    "верх-лево": "zone.tl", "верх-центр": "zone.tc", "верх-право": "zone.tr",
    "центр-лево": "zone.ml", "центр": "zone.mc", "центр-право": "zone.mr",
    "низ-лево": "zone.bl", "низ-центр": "zone.bc", "низ-право": "zone.br",
  };

  const LINE_PHRASES = [
    ["EXIF: отсутствует", "osint.exifMissing"],
    ["EXIF отсутствует — возможна пересылка или экспорт из генератора", "osint.noExifHint"],
    ["EXIF: ошибка чтения", "osint.exifError"],
    ["ПО генератора", "evCat.generator"],
    ["Метаданные камеры", "evCat.cameraMeta"],
    ["Метаданные", "evCat.metadata"],
    ["Геометрия", "evCat.geometry"],
    ["Артефакты", "evCat.artifacts"],
    ["Визуальная синтетика", "evCat.visualSynth"],
    ["Метаданные видео", "evCat.videoMeta"],
    ["Аудиодорожка", "evCat.audioTrack"],
    ["Кадры", "evCat.frames"],
    ["Стабильность кадров", "evCat.frameStability"],
    ["ELA", "evCat.ela"],
  ];

  function regionLabel(region) {
    if (!region) return t("zone.unknown");
    const key = REGION_MAP[region] || REGION_MAP[region.toLowerCase?.()];
    return key ? t(key) : region;
  }

  function severityLabel(sev) {
    const k = `severity.${sev || "minor"}`;
    return messages[lang][k] ? t(k) : (sev || "minor");
  }

  function riskWord(ai) {
    const n = Number(ai);
    if (n >= 65) return t("report.risk.high");
    if (n >= 42) return t("report.risk.moderate");
    return t("report.risk.low");
  }

  function riskLevelWord(ai) {
    const n = Number(ai);
    if (n >= 60) return t("report.riskLevel.high");
    if (n >= 35) return t("report.riskLevel.moderate");
    return t("report.riskLevel.low");
  }

  function translateLine(text) {
    if (!text || lang === "ru") return text || "";
    let s = String(text);
    LINE_PHRASES.forEach(([from, key]) => {
      if (s.includes(from)) s = s.split(from).join(t(key));
    });
    const res = s.match(/Разрешение:\s*(\d+)×(\d+)\s*\(([^)]+)\s*MP\)/);
    if (res) s = s.replace(res[0], t("osint.resolution", { w: res[1], h: res[2], mp: res[3] }));
    const cam = s.match(/Камера \(EXIF\):\s*(.+)/);
    if (cam) s = s.replace(cam[0], t("osint.camera", { model: cam[1] }));
    const fmt = s.match(/Формат:\s*(.+)/);
    if (fmt) s = s.replace(fmt[0], t("osint.format", { fmt: fmt[1] }));
    const dur = s.match(/Длительность:\s*([\d.]+)\s*с/);
    if (dur) s = s.replace(dur[0], t("osint.duration", { dur: dur[1] }));
    const fps = s.match(/^FPS:\s*(.+)$/m);
    if (fps) s = s.replace(fps[0], t("osint.fps", { fps: fps[1] }));
    if (s.startsWith("Аудио: ")) {
      const val = s.slice(7);
      s = t("osint.audio", { val: val === "да" ? t("report.audio.yes") : val === "нет" ? t("report.audio.no") : val });
    }
    if (s.startsWith("Зона: ")) s = t("ev.zone", { region: regionLabel(s.slice(6)) });
    if (s.startsWith("Плагиат: ")) s = t("ev.plagiarism", { cat: translateLine(s.slice(9)) });
    return s;
  }

  function translateEvidenceCategory(cat) {
    if (!cat) return "";
    if (lang === "ru") return cat;
    if (cat.startsWith("Зона: ")) return t("ev.zone", { region: regionLabel(cat.slice(6)) });
    if (cat.startsWith("Плагиат: ")) return t("ev.plagiarism", { cat: translateEvidenceCategory(cat.slice(9)) });
    return translateLine(cat);
  }

  function buildReasoningFromReport(r) {
    const scores = r.scores || {};
    const metrics = r.metrics || {};
    const ai = Number(scores.ai ?? 0);
    const pl = Number(scores.plagiarism ?? 0);
    const conf = Number(r.confidence ?? 0);
    const auth = Math.max(0, 100 - Math.round(ai));
    const verdict = verdictLabel(r.verdict, r.verdict_label);
    const evidence = r.evidence || [];
    const critical = evidence.filter((e) => e.severity === "critical").length;
    const moderate = evidence.filter((e) => e.severity === "moderate").length;
    const segments = r.segments || [];
    const zones = r.zones || [];
    const categories = r.category_scores || {};
    const ct = r.content_type || "text";

    const parts = [
      t("report.summary.line1", { verdict, ai: Math.round(ai), risk: riskWord(ai), auth, pl: Math.round(pl), conf }),
      t("report.summary.line2", { critical, moderate }),
    ];
    if (ct === "text") parts.push(t("report.summary.sentences", { n: segments.length }));
    else if (ct === "image") {
      parts.push(t("report.summary.image", {
        res: `${metrics.width ?? "?"}×${metrics.height ?? "?"}`,
        mp: metrics.megapixels ?? "?",
        zones: zones.length || metrics.zones_analyzed || 9,
      }));
      const entries = Object.entries(categories);
      if (entries.length) {
        const top = entries.sort((a, b) => b[1] - a[1])[0];
        parts.push(t("report.summary.imageCat", { cat: categoryLabel(top[0]), val: top[1] }));
      }
    } else if (ct === "video") {
      parts.push(t("report.summary.video", {
        dur: metrics.duration_sec ?? "?",
        fps: metrics.fps ?? "?",
        frames: metrics.frames_analyzed ?? 0,
        zones: zones.length,
      }));
      if (categories.sync != null) {
        parts.push(t("report.summary.videoBio", { bio: categories.biometrics ?? "—", sync: categories.sync }));
      }
    }
    parts.push(t("report.summary.engine", { mode: metrics.analysis_engine || r.analysis_mode || "hybrid" }));

    const aiParts = [t("report.ai.open", { ai: Math.round(ai), level: riskLevelWord(ai) })];
    if (ct === "image" || ct === "video") {
      if (Object.keys(categories).length) {
        const cats = Object.entries(categories).sort((a, b) => b[1] - a[1]).slice(0, 4)
          .map(([k, v]) => `${categoryLabel(k)}: ${v}`).join(", ");
        aiParts.push(t("report.ai.cats", { cats }));
      }
      if (zones.length) {
        const hot = [...zones].sort((a, b) => (b.ai_score ?? 0) - (a.ai_score ?? 0)).slice(0, 3)
          .map((z) => `${regionLabel(z.region)} (${Math.round(z.ai_score ?? 0)}%)`).join("; ");
        aiParts.push(t("report.ai.zones", { zones: hot }));
      }
    } else {
      const flagged = segments.filter((s) => (s.ai_score ?? 0) >= 35);
      if (flagged.length) aiParts.push(t("report.ai.flags", { n: flagged.length, total: segments.length }));
      if (critical) aiParts.push(t("report.ai.critical", { n: critical }));
    }

    let plText;
    if (ct === "image") {
      plText = t("report.pl.image", {
        pl: Math.round(pl),
        ela: metrics.ela_variance ?? "—",
        exif: metrics.exif_present ? t("report.exif.yes") : t("report.exif.no"),
      });
    } else if (ct === "video") {
      plText = t("report.pl.video", {
        pl: Math.round(pl),
        var: metrics.frame_score_variance ?? "—",
        audio: metrics.has_audio ? t("report.audio.yes") : t("report.audio.no"),
      });
    } else if (pl < 20) {
      plText = t("report.pl.low", { pl: Math.round(pl) });
    } else {
      const flagged = segments.filter((s) => (s.plagiarism_score ?? 0) >= 35);
      plText = t("report.pl.flagged", { pl: Math.round(pl), n: flagged.length });
    }

    return {
      summary: parts.join(" "),
      ai_analysis: aiParts.join(" "),
      plagiarism_analysis: plText,
      conclusion: t("report.conclusion", {
        verdict, conf, ai: Math.round(ai), pl: Math.round(pl), auth,
      }),
    };
  }

  function localizedReasoning(r) {
    if (lang === "ru") return r.reasoning || {};
    return buildReasoningFromReport(r);
  }

  function localizedCompareSummary(comparison, reportA, reportB, nameA, nameB) {
    if (!comparison) return "";
    if (lang === "ru") return comparison.summary || "";
    const labelA = nameA || "A";
    const labelB = nameB || "B";
    const sa = reportA?.scores || {};
    const sb = reportB?.scores || {};
    const aiA = Math.round(sa.ai ?? 0);
    const aiB = Math.round(sb.ai ?? 0);
    const authA = Math.round(sa.authenticity ?? Math.max(0, 100 - aiA));
    const authB = Math.round(sb.authenticity ?? Math.max(0, 100 - aiB));
    const lines = [
      t("compare.line", { name: labelA, verdict: verdictLabel(reportA?.verdict, reportA?.verdict_label), ai: aiA, auth: authA }),
      t("compare.line", { name: labelB, verdict: verdictLabel(reportB?.verdict, reportB?.verdict_label), ai: aiB, auth: authB }),
    ];
    if (comparison.verdict_match) lines.push(t("compare.match"));
    else lines.push(t("compare.differ"));
    lines.push(t("compare.delta", { ai: comparison.ai_delta ?? 0, pl: comparison.plagiarism_delta ?? 0 }));
    const aiDelta = comparison.ai_delta ?? 0;
    if (aiDelta >= 25) {
      lines.push(t("compare.gapHigh", { riskier: comparison.higher_ai_risk || labelA, safer: comparison.lower_ai_risk || labelB }));
    } else if (aiDelta >= 10) {
      lines.push(t("compare.gapModerate"));
    }
    return lines.join(" ");
  }

  function osintRecommendations(contentType) {
    if (contentType === "image") return [t("osint.rec.img1"), t("osint.rec.img2"), t("osint.rec.img3")];
    if (contentType === "video") return [t("osint.rec.vid1"), t("osint.rec.vid2")];
    if (contentType === "text") return [t("osint.rec.txt1"), t("osint.rec.txt2")];
    return [t("osint.rec.empty")];
  }

  function applyDom() {
    document.documentElement.lang = lang === "uz" ? "uz" : lang;
    document.title = t("app.title");
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      if (el.dataset.filename === "1") return;
      const key = el.getAttribute("data-i18n");
      const attr = el.getAttribute("data-i18n-attr");
      const val = t(key);
      if (attr) el.setAttribute(attr, val);
      else el.textContent = val;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
    });
    document.querySelectorAll(".lang-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });
    const theme = getTheme();
    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) themeBtn.textContent = theme === "light" ? t("theme.dark") : t("theme.light");
  }

  function setLang(l) {
    if (!messages[l]) return;
    lang = l;
    localStorage.setItem(STORAGE_LANG, l);
    applyDom();
    window.dispatchEvent(new CustomEvent("forensai:lang"));
  }

  function getLang() {
    return lang;
  }

  function getTheme() {
    return localStorage.getItem(STORAGE_THEME) || "dark";
  }

  function setTheme(theme) {
    const next = theme === "light" ? "light" : "dark";
    localStorage.setItem(STORAGE_THEME, next);
    document.documentElement.setAttribute("data-theme", next);
    const themeBtn = document.getElementById("themeToggle");
    if (themeBtn) themeBtn.textContent = next === "light" ? t("theme.dark") : t("theme.light");
  }

  function toggleTheme() {
    setTheme(getTheme() === "dark" ? "light" : "dark");
  }

  function initTheme() {
    document.documentElement.setAttribute("data-theme", getTheme());
  }

  initTheme();

  const params = new URLSearchParams(location.search);
  if (params.get("ref")) localStorage.setItem("forensai_pending_ref", params.get("ref").toUpperCase());

  window.I18n = {
    t, setLang, getLang, applyDom, verdictLabel, categoryLabel, getTheme, setTheme, toggleTheme, messages,
    regionLabel, severityLabel, translateLine, translateEvidenceCategory, localizedReasoning,
    localizedCompareSummary, osintRecommendations,
  };
})();
