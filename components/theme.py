"""
Sentio Training App - Premium Theme

Agricultural Data Observatory aesthetic with:
- Distinctive typography (no generic fonts)
- Bold color palette with organic accents
- Glass-morphism cards with glow effects
- Smooth animations and transitions
"""


def get_theme_css():
    """
    Returns the complete CSS theme for the training app.

    Design principles from frontend-design skill:
    1. Typography: Playfair Display (headers) + DM Sans (body) + JetBrains Mono (data)
    2. Color: Bold greens/reds with warm amber accents on dark background
    3. Motion: Animated pipeline, hover glows, staggered reveals
    4. Polish: Glass-morphism, gradient mesh, noise texture
    """
    return """
    <style>
        /* === GOOGLE FONTS === */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        /* === CSS CUSTOM PROPERTIES === */
        :root {
            /* Background colors */
            --bg-deep: #0d1117;
            --bg-surface: #161b22;
            --bg-elevated: #1c2128;
            --bg-hover: #21262d;

            /* Accent colors */
            --accent-healthy: #7ee787;
            --accent-sick: #f85149;
            --accent-warn: #f0883e;
            --accent-info: #58a6ff;

            /* Text colors */
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;

            /* Borders */
            --border-default: rgba(240, 246, 252, 0.1);
            --border-focus: rgba(126, 231, 135, 0.4);

            /* Glows */
            --glow-healthy: 0 0 20px rgba(126, 231, 135, 0.25);
            --glow-sick: 0 0 20px rgba(248, 81, 73, 0.25);
            --glow-warn: 0 0 20px rgba(240, 136, 62, 0.25);

            /* Typography */
            --font-display: 'Playfair Display', Georgia, serif;
            --font-body: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', 'SF Mono', monospace;

            /* Spacing */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;

            /* Transitions */
            --transition-fast: 150ms ease;
            --transition-normal: 250ms ease;
            --transition-slow: 400ms ease;
        }

        /* === GLOBAL STYLES === */
        .stApp {
            background: var(--bg-deep);
        }

        /* Gradient mesh background overlay */
        .stApp::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background:
                radial-gradient(ellipse at 20% 0%, rgba(126, 231, 135, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(88, 166, 255, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 40% 50%, rgba(248, 81, 73, 0.03) 0%, transparent 40%);
            pointer-events: none;
            z-index: 0;
        }

        /* Noise texture overlay */
        .stApp::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
            opacity: 0.03;
            pointer-events: none;
            z-index: 0;
        }

        /* === TYPOGRAPHY === */
        h1, h2, h3, .main-title {
            font-family: var(--font-display) !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.02em;
        }

        p, span, div, label {
            font-family: var(--font-body) !important;
        }

        code, pre, .metric-value {
            font-family: var(--font-mono) !important;
        }

        /* Main header */
        .observatory-header {
            font-family: var(--font-display);
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text-primary);
            text-align: center;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }

        .observatory-subtitle {
            font-family: var(--font-body);
            font-size: 1rem;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 1.5rem;
        }

        /* === CARD COMPONENTS === */
        .glass-card {
            background: rgba(22, 27, 34, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--border-default);
            border-radius: 12px;
            padding: var(--spacing-lg);
            transition: all var(--transition-normal);
        }

        .glass-card:hover {
            border-color: var(--border-focus);
            box-shadow: var(--glow-healthy);
            transform: translateY(-2px);
        }

        .glass-card-healthy {
            border-color: rgba(126, 231, 135, 0.3);
        }

        .glass-card-healthy:hover {
            box-shadow: var(--glow-healthy);
        }

        .glass-card-sick {
            border-color: rgba(248, 81, 73, 0.3);
        }

        .glass-card-sick:hover {
            box-shadow: var(--glow-sick);
        }

        /* === DATA FLOW PIPELINE === */
        .pipeline-container {
            background: var(--bg-surface);
            border-radius: 16px;
            padding: var(--spacing-xl);
            padding-bottom: var(--spacing-lg);  /* Normal padding - feedback loop is inside */
            margin-bottom: var(--spacing-xl);
            border: 1px solid var(--border-default);
            position: relative;
            overflow: visible;
        }

        .pipeline-title {
            font-family: var(--font-display);
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: var(--spacing-lg);
            text-align: center;
        }

        .pipeline-stages {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: var(--spacing-md);
        }

        .pipeline-stage {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            flex: 1;
            position: relative;
        }

        .stage-icon {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: var(--spacing-sm);
            background: var(--bg-elevated);
            border: 2px solid var(--border-default);
            transition: all var(--transition-normal);
        }

        .stage-icon.active {
            border-color: var(--accent-healthy);
            background: rgba(126, 231, 135, 0.25);  /* Visible fill */
            box-shadow:
                0 0 0 4px rgba(126, 231, 135, 0.3),  /* Inner ring */
                0 0 30px rgba(126, 231, 135, 0.6);   /* Outer glow */
            transform: scale(1.2);
            animation: active-pulse 1.5s ease-in-out infinite;
        }

        .stage-icon.completed {
            border-color: var(--accent-healthy);
            background: rgba(126, 231, 135, 0.15);
            position: relative;
        }

        /* Checkmark badge for completed stages */
        .stage-icon.completed::after {
            content: '\2713';  /* Unicode checkmark */
            position: absolute;
            bottom: -2px;
            right: -2px;
            background: var(--accent-healthy);
            color: var(--bg-deep);
            font-size: 0.6rem;
            font-weight: bold;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        /* VERIFIED stage special styling - gold glow */
        .stage-icon.active.verified-stage {
            border-color: var(--accent-warn);
            background: rgba(240, 136, 62, 0.25);  /* Golden fill */
            box-shadow:
                0 0 0 4px rgba(240, 136, 62, 0.3),  /* Inner ring */
                0 0 30px rgba(240, 136, 62, 0.6);   /* Outer glow */
            animation: verified-pulse 1.5s ease-in-out infinite;
        }

        /* AI loading spinner overlay - blue theme */
        .stage-icon.loading {
            position: relative;
            border-color: var(--accent-info) !important;
            background: rgba(88, 166, 255, 0.25) !important;  /* Blue fill */
            box-shadow:
                0 0 0 4px rgba(88, 166, 255, 0.3),
                0 0 30px rgba(88, 166, 255, 0.5) !important;
            animation: ai-pulse 1.5s ease-in-out infinite !important;
        }

        .stage-icon.loading::after {
            content: '';
            position: absolute;
            inset: -6px;
            border: 3px solid transparent;
            border-top-color: var(--accent-info);
            border-radius: 50%;
            animation: spinner-rotate 0.8s linear infinite;
        }

        @keyframes spinner-rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes ai-pulse {
            0%, 100% {
                box-shadow:
                    0 0 0 4px rgba(88, 166, 255, 0.3),
                    0 0 25px rgba(88, 166, 255, 0.5);
                transform: scale(1.15);
            }
            50% {
                box-shadow:
                    0 0 0 6px rgba(88, 166, 255, 0.4),
                    0 0 40px rgba(88, 166, 255, 0.7);
                transform: scale(1.22);
            }
        }

        @keyframes active-pulse {
            0%, 100% {
                box-shadow:
                    0 0 0 4px rgba(126, 231, 135, 0.3),
                    0 0 25px rgba(126, 231, 135, 0.5);
                transform: scale(1.15);
            }
            50% {
                box-shadow:
                    0 0 0 6px rgba(126, 231, 135, 0.4),
                    0 0 45px rgba(126, 231, 135, 0.8);  /* Much brighter at peak */
                transform: scale(1.25);
            }
        }

        @keyframes verified-pulse {
            0%, 100% {
                box-shadow:
                    0 0 0 4px rgba(240, 136, 62, 0.3),
                    0 0 25px rgba(240, 136, 62, 0.5);
                transform: scale(1.15);
            }
            50% {
                box-shadow:
                    0 0 0 6px rgba(240, 136, 62, 0.4),
                    0 0 45px rgba(240, 136, 62, 0.8);  /* Golden glow at peak */
                transform: scale(1.25);
            }
        }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 10px rgba(126, 231, 135, 0.2); }
            50% { box-shadow: 0 0 25px rgba(126, 231, 135, 0.4); }
        }

        /* Stage guidance panel */
        .stage-guidance {
            position: absolute;
            top: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-elevated);
            border: 1px solid var(--border-focus);
            border-radius: 8px;
            padding: 8px 16px;
            white-space: nowrap;
            font-family: var(--font-body);
            font-size: 0.75rem;
            color: var(--text-primary);
            z-index: 10;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .stage-guidance::before {
            content: '';
            position: absolute;
            top: -6px;
            left: 50%;
            transform: translateX(-50%);
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-bottom: 6px solid var(--border-focus);
        }

        .guidance-arrow {
            display: inline-block;
            animation: bounce-arrow 1s ease-in-out infinite;
            margin-right: 4px;
        }

        @keyframes bounce-arrow {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(3px); }
        }

        .stage-name {
            font-family: var(--font-body);
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .stage-desc {
            font-family: var(--font-body);
            font-size: 0.75rem;
            color: var(--text-muted);
            max-width: 100px;
        }

        /* Pipeline connectors */
        .pipeline-connector {
            flex: 0.3;
            height: 2px;
            background: linear-gradient(90deg,
                var(--border-default) 0%,
                var(--accent-healthy) 50%,
                var(--border-default) 100%);
            position: relative;
            overflow: hidden;
        }

        .pipeline-connector::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 50%;
            height: 100%;
            background: linear-gradient(90deg,
                transparent 0%,
                var(--accent-healthy) 50%,
                transparent 100%);
            animation: flow-particle 2s linear infinite;
        }

        @keyframes flow-particle {
            0% { left: -50%; }
            100% { left: 150%; }
        }

        /* Feedback loop visual - inside container, not absolute positioned */
        .feedback-loop-container {
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px dashed rgba(240, 136, 62, 0.3);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
        }

        .feedback-loop-svg {
            width: 85%;  /* Centered, not full width */
            height: 35px;  /* Proportional height */
            max-width: 700px;
            overflow: visible;
        }

        .feedback-loop-path {
            stroke: var(--accent-warn);
            stroke-width: 2;
            fill: none;
            stroke-dasharray: 6, 4;
            animation: dash-flow 1s linear infinite;
        }

        @keyframes dash-flow {
            to {
                stroke-dashoffset: -10;
            }
        }

        .feedback-loop-arrow {
            fill: var(--accent-warn);
        }

        .feedback-loop-text {
            font-family: var(--font-body);
            font-size: 0.75rem;
            color: var(--accent-warn);
            white-space: nowrap;
        }

        /* Animated particle on feedback loop */
        .feedback-particle {
            fill: var(--accent-warn);
            filter: drop-shadow(0 0 4px rgba(240, 136, 62, 0.8));
        }

        /* Feedback loop badge */
        .feedback-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(240, 136, 62, 0.15);
            border: 1px solid rgba(240, 136, 62, 0.3);
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 0.75rem;
            color: var(--accent-warn);
            font-family: var(--font-body);
        }

        .feedback-badge-icon {
            animation: spin-slow 3s linear infinite;
        }

        @keyframes spin-slow {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Legacy text-only feedback loop (fallback) */
        .feedback-loop {
            font-family: var(--font-body);
            font-size: 0.75rem;
            color: var(--accent-warn);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* === PREDICTION DISPLAY === */
        .prediction-healthy {
            font-family: var(--font-display);
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-healthy);
            text-shadow: var(--glow-healthy);
        }

        .prediction-sick {
            font-family: var(--font-display);
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-sick);
            text-shadow: var(--glow-sick);
        }

        /* === METRICS === */
        .metric-container {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .metric-label {
            font-family: var(--font-body);
            font-size: 0.75rem;
            font-weight: 500;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            font-family: var(--font-mono);
            font-size: 1.5rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        .metric-value-healthy {
            color: var(--accent-healthy);
        }

        .metric-value-sick {
            color: var(--accent-sick);
        }

        /* === BUTTONS === */
        .stButton > button {
            font-family: var(--font-body) !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            transition: all var(--transition-normal) !important;
        }

        /* Primary button (Correct) */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent-healthy) 0%, #4ade80 100%) !important;
            color: var(--bg-deep) !important;
            border: none !important;
        }

        .stButton > button[kind="primary"]:hover {
            box-shadow: var(--glow-healthy) !important;
            transform: translateY(-2px) !important;
        }

        /* Secondary button (Incorrect) */
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            color: var(--accent-sick) !important;
            border: 2px solid var(--accent-sick) !important;
        }

        .stButton > button[kind="secondary"]:hover {
            background: rgba(248, 81, 73, 0.1) !important;
            box-shadow: var(--glow-sick) !important;
        }

        /* === FILE LOCATION PANEL === */
        .file-location {
            background: var(--bg-elevated);
            border-radius: 8px;
            padding: var(--spacing-md);
            border: 1px solid var(--border-default);
            font-family: var(--font-mono);
        }

        .file-location-header {
            font-family: var(--font-body);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--spacing-sm);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .file-path {
            font-family: var(--font-mono);
            font-size: 0.875rem;
            color: var(--text-primary);
            word-break: break-all;
        }

        .file-destination {
            margin-top: var(--spacing-sm);
            padding-top: var(--spacing-sm);
            border-top: 1px dashed var(--border-default);
        }

        .destination-healthy {
            color: var(--accent-healthy);
        }

        .destination-sick {
            color: var(--accent-sick);
        }

        /* === ACTIVITY LOG === */
        .activity-log {
            background: var(--bg-elevated);
            border-radius: 8px;
            padding: var(--spacing-md);
            border: 1px solid var(--border-default);
            max-height: 300px;
            overflow-y: auto;
        }

        .activity-log-header {
            font-family: var(--font-body);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: var(--spacing-md);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .activity-item {
            display: flex;
            align-items: flex-start;
            gap: var(--spacing-sm);
            padding: var(--spacing-sm) 0;
            border-bottom: 1px solid var(--border-default);
            animation: fade-in 0.3s ease;
        }

        .activity-item:last-child {
            border-bottom: none;
        }

        @keyframes fade-in {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .activity-time {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            flex-shrink: 0;
        }

        .activity-icon {
            font-size: 1rem;
            flex-shrink: 0;
        }

        .activity-text {
            font-family: var(--font-body);
            font-size: 0.8125rem;
            color: var(--text-secondary);
        }

        .activity-detail {
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* === SIDEBAR === */
        [data-testid="stSidebar"] {
            background: var(--bg-surface) !important;
            border-right: 1px solid var(--border-default) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
            font-family: var(--font-display) !important;
            color: var(--text-primary) !important;
        }

        /* Sidebar metrics */
        [data-testid="stSidebar"] [data-testid="stMetricValue"] {
            font-family: var(--font-mono) !important;
            color: var(--text-primary) !important;
        }

        /* === PROGRESS BAR === */
        .stProgress > div > div {
            background: linear-gradient(90deg, var(--accent-healthy), var(--accent-info)) !important;
        }

        .stProgress {
            height: 6px !important;
        }

        /* === TABS === */
        .stTabs [data-baseweb="tab-list"] {
            gap: var(--spacing-xs);
            background: var(--bg-surface);
            border-radius: 8px;
            padding: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            font-family: var(--font-body) !important;
            font-weight: 500 !important;
            color: var(--text-secondary) !important;
            background: transparent !important;
            border-radius: 6px !important;
            padding: var(--spacing-sm) var(--spacing-md) !important;
        }

        .stTabs [aria-selected="true"] {
            background: var(--bg-elevated) !important;
            color: var(--text-primary) !important;
        }

        /* === EXPANDERS === */
        .streamlit-expanderHeader {
            font-family: var(--font-body) !important;
            font-weight: 500 !important;
            color: var(--text-primary) !important;
            background: var(--bg-surface) !important;
            border-radius: 8px !important;
        }

        /* Fix expander stacking and overlap - increased margins */
        [data-testid="stExpander"] {
            position: relative;
            z-index: 1;
            margin-bottom: 1rem;  /* Increased from var(--spacing-sm) for better separation */
        }

        [data-testid="stExpander"]:hover {
            z-index: 2;
        }

        [data-testid="stExpander"] > details {
            background: var(--bg-surface);
            border: 1px solid var(--border-default);
            border-radius: 8px;
            overflow: hidden;
        }

        [data-testid="stExpander"] > details > summary {
            padding: 1rem;  /* Increased padding for better spacing */
            padding-right: 2.5rem;  /* Space for toggle icon on right */
            display: flex;
            align-items: center;
            gap: 0.5rem;  /* Space for emoji icons */
            position: relative;
        }

        /* Ensure summary text doesn't overlap with toggle icon */
        [data-testid="stExpander"] > details > summary > span {
            flex: 1;
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            padding-right: 1rem;
        }

        [data-testid="stExpander"] > details[open] > div {
            padding: var(--spacing-md);
            padding-top: 0;
            border-top: 1px solid var(--border-default);
        }

        /* === INFO/SUCCESS/WARNING/ERROR === */
        .stAlert {
            border-radius: 8px !important;
            font-family: var(--font-body) !important;
        }

        /* === AUDIO PLAYER === */
        audio {
            width: 100%;
            border-radius: 8px;
            background: var(--bg-elevated);
        }

        /* === IMAGES === */
        .stImage {
            border-radius: 12px;
            overflow: hidden;
        }

        /* === HOW IT WORKS SECTIONS === */
        .how-it-works {
            background: var(--bg-elevated);
            border-radius: 8px;
            padding: var(--spacing-lg);
            border: 1px solid var(--border-default);
            margin: var(--spacing-md) 0;
        }

        .how-it-works-title {
            font-family: var(--font-body);
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--accent-info);
            margin-bottom: var(--spacing-md);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .how-it-works-content {
            font-family: var(--font-body);
            font-size: 0.8125rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }

        /* === STAGGERED REVEAL ANIMATION === */
        @keyframes stagger-reveal {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .stagger-1 { animation: stagger-reveal 0.4s ease forwards; animation-delay: 0.1s; opacity: 0; }
        .stagger-2 { animation: stagger-reveal 0.4s ease forwards; animation-delay: 0.2s; opacity: 0; }
        .stagger-3 { animation: stagger-reveal 0.4s ease forwards; animation-delay: 0.3s; opacity: 0; }
        .stagger-4 { animation: stagger-reveal 0.4s ease forwards; animation-delay: 0.4s; opacity: 0; }
        .stagger-5 { animation: stagger-reveal 0.4s ease forwards; animation-delay: 0.5s; opacity: 0; }

        /* === UTILITY CLASSES === */
        .text-muted {
            color: var(--text-muted) !important;
        }

        .text-secondary {
            color: var(--text-secondary) !important;
        }

        /* === SCROLLBAR STYLING === */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-deep);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border-default);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
    </style>
    """


def get_light_theme_css():
    """
    Returns CSS overrides for light mode.

    Inverts the color scheme while keeping accent colors intact
    for health coding (green=healthy, red=sick).
    """
    return """
    <style>
        /* === LIGHT MODE OVERRIDES === */
        :root {
            /* Background colors - light mode */
            --bg-deep: #ffffff;
            --bg-surface: #f6f8fa;
            --bg-elevated: #ffffff;
            --bg-hover: #f0f2f5;

            /* Text colors - inverted for light mode */
            --text-primary: #1f2328;
            --text-secondary: #57606a;
            --text-muted: #57606a;  /* Fixed: was #8b949e - too light on white */

            /* Borders - darker for light backgrounds */
            --border-default: rgba(31, 35, 40, 0.15);
            --border-focus: rgba(46, 160, 67, 0.4);

            /* Accent colors stay the same for health coding */
            --accent-healthy: #1a7f37;
            --accent-sick: #cf222e;
            --accent-warn: #bf5700;
            --accent-info: #0969da;

            /* Glows - adjusted for light mode */
            --glow-healthy: 0 0 20px rgba(26, 127, 55, 0.15);
            --glow-sick: 0 0 20px rgba(207, 34, 46, 0.15);
            --glow-warn: 0 0 20px rgba(191, 87, 0, 0.15);
        }

        /* Override app background */
        .stApp {
            background: var(--bg-deep) !important;
        }

        /* Subtle gradient mesh for light mode */
        .stApp::before {
            background:
                radial-gradient(ellipse at 20% 0%, rgba(26, 127, 55, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(9, 105, 218, 0.04) 0%, transparent 50%),
                radial-gradient(ellipse at 40% 50%, rgba(207, 34, 46, 0.02) 0%, transparent 40%) !important;
        }

        /* Less visible noise texture in light mode */
        .stApp::after {
            opacity: 0.015 !important;
        }

        /* Glass cards for light mode */
        .glass-card {
            background: rgba(255, 255, 255, 0.9) !important;
            border-color: var(--border-default) !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        }

        .glass-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        }

        /* Pipeline container */
        .pipeline-container {
            background: var(--bg-surface) !important;
            border-color: var(--border-default) !important;
        }

        /* Stage icons */
        .stage-icon {
            background: var(--bg-elevated) !important;
            border-color: var(--border-default) !important;
        }

        .stage-icon.active {
            border-color: var(--accent-healthy) !important;
        }

        .stage-icon.completed {
            background: rgba(26, 127, 55, 0.1) !important;
        }

        /* File location panel */
        .file-location {
            background: var(--bg-elevated) !important;
            border-color: var(--border-default) !important;
        }

        /* Activity log */
        .activity-log {
            background: var(--bg-elevated) !important;
            border-color: var(--border-default) !important;
        }

        .activity-item {
            border-color: var(--border-default) !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: var(--bg-surface) !important;
            border-right-color: var(--border-default) !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: var(--bg-surface) !important;
        }

        .stTabs [aria-selected="true"] {
            background: var(--bg-elevated) !important;
        }

        /* Scrollbar for light mode */
        ::-webkit-scrollbar-track {
            background: var(--bg-surface) !important;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.2) !important;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 0, 0, 0.3) !important;
        }

        /* Prediction text adjustments */
        .prediction-healthy {
            color: var(--accent-healthy) !important;
            text-shadow: none !important;
        }

        .prediction-sick {
            color: var(--accent-sick) !important;
            text-shadow: none !important;
        }

        /* How it works sections */
        .how-it-works {
            background: var(--bg-elevated) !important;
            border-color: var(--border-default) !important;
        }

        /* === LIGHT MODE TEXT VISIBILITY FIXES === */
        /* Primary text elements - must be visible in light mode */
        .pipeline-title,
        .stage-name,
        .metric-value,
        .activity-text,
        .how-it-works-content,
        .how-it-works-title,
        .file-path,
        .file-location-header {
            color: var(--text-primary) !important;
        }

        /* Secondary/muted text elements */
        .stage-desc,
        .activity-detail,
        .activity-time,
        .metric-label {
            color: var(--text-secondary) !important;
        }

        /* Streamlit native elements - tabs */
        .stTabs [data-baseweb="tab"] {
            color: var(--text-secondary) !important;
        }

        .stTabs [aria-selected="true"] {
            color: var(--text-primary) !important;
        }

        /* Streamlit metric values */
        [data-testid="stMetricValue"] {
            color: var(--text-primary) !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-secondary) !important;
        }

        /* Markdown text */
        .stMarkdown,
        .stMarkdown p,
        .stMarkdown span {
            color: var(--text-primary) !important;
        }

        /* Expander text */
        .streamlit-expanderHeader,
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary span {
            color: var(--text-primary) !important;
        }

        /* Info/how-it-works title keeps accent color */
        .how-it-works-title {
            color: var(--accent-info) !important;
        }

        /* Feedback loop text */
        .feedback-loop,
        .feedback-loop-text {
            color: var(--accent-warn) !important;
        }
    </style>
    """


def apply_theme(st, mode: str = 'dark'):
    """
    Apply the custom theme to a Streamlit app.

    Args:
        st: Streamlit module instance
        mode: 'dark' or 'light' (default: 'dark')
    """
    st.markdown(get_theme_css(), unsafe_allow_html=True)
    if mode == 'light':
        st.markdown(get_light_theme_css(), unsafe_allow_html=True)


def apply_light_theme(st):
    """
    Apply the light mode theme to a Streamlit app.

    Args:
        st: Streamlit module instance
    """
    apply_theme(st, mode='light')
