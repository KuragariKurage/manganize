/**
 * Icon library for toast notifications
 * Using Heroicons style (https://heroicons.com/)
 */

const icons = {
    success: `
    <svg viewBox="0 0 16 16" style="width: 16px; height: 16px;">
      <rect x="1" y="1" width="14" height="14" fill="#90ee90" stroke="#008000" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <path d="M4 8l2 2 4-4" stroke="#008000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `,
    error: `
    <svg viewBox="0 0 16 16" style="width: 16px; height: 16px;">
      <rect x="1" y="1" width="14" height="14" fill="#ffb6c1" stroke="#ff0000" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <path d="M5 5l6 6M11 5l-6 6" stroke="#ff0000" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `,
    info: `
    <svg viewBox="0 0 16 16" style="width: 16px; height: 16px;">
      <rect x="1" y="1" width="14" height="14" fill="#87ceeb" stroke="#000080" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <circle cx="8" cy="5" r="1" fill="#000080"/>
      <rect x="7" y="7" width="2" height="4" fill="#000080"/>
    </svg>
  `,
    warning: `
    <svg viewBox="0 0 16 16" style="width: 16px; height: 16px;">
      <rect x="1" y="1" width="14" height="14" fill="#ffffe0" stroke="#808000" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <path d="M8 4l0 4" stroke="#808000" stroke-width="2" stroke-linecap="round"/>
      <circle cx="8" cy="10" r="1" fill="#808000"/>
    </svg>
  `,
    close: `
    <svg viewBox="0 0 12 12" style="width: 12px; height: 12px;">
      <rect x="0" y="0" width="12" height="12" fill="#c0c0c0" stroke="#808080" stroke-width="1"/>
      <rect x="1" y="1" width="10" height="10" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <path d="M3 3l6 6M9 3l-6 6" stroke="#000000" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
  `
};

// Additional XP-style icons for toolbar
const toolbarIcons = {
    home: `
    <svg viewBox="0 0 16 16" style="width: 12px; height: 12px;">
      <rect x="1" y="1" width="14" height="14" fill="#f0f0f0" stroke="#808080" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <polygon points="8,4 12,8 4,8" fill="#000080"/>
      <rect x="6" y="8" width="4" height="4" fill="#000080"/>
    </svg>
  `,
    history: `
    <svg viewBox="0 0 16 16" style="width: 12px; height: 12px;">
      <rect x="1" y="1" width="14" height="14" fill="#f0f0f0" stroke="#808080" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <circle cx="8" cy="8" r="5" fill="none" stroke="#000080" stroke-width="1.5"/>
      <path d="M8 5v3l2 1" stroke="#000080" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
  `,
    character: `
    <svg viewBox="0 0 16 16" style="width: 12px; height: 12px;">
      <rect x="1" y="1" width="14" height="14" fill="#f0f0f0" stroke="#808080" stroke-width="1"/>
      <rect x="2" y="2" width="12" height="12" fill="#ffffff" stroke="#c0c0c0" stroke-width="1"/>
      <circle cx="8" cy="5" r="2" fill="#000080"/>
      <rect x="6" y="7" width="4" height="4" fill="#000080"/>
    </svg>
  `,
    minimize: `
    <svg viewBox="0 0 8 6" style="width: 6px; height: 4px;">
      <rect x="0" y="2" width="8" height="2" fill="#000000"/>
    </svg>
  `,
    maximize: `
    <svg viewBox="0 0 8 8" style="width: 6px; height: 6px;">
      <rect x="0" y="0" width="8" height="8" fill="none" stroke="#000000" stroke-width="1"/>
      <rect x="2" y="2" width="4" height="4" fill="#000000"/>
    </svg>
  `,
    close: `
    <svg viewBox="0 0 8 8" style="width: 6px; height: 6px;">
      <path d="M1 1l6 6M7 1l-6 6" stroke="#000000" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
  `
};

// Export for use in Alpine.js components
window.getIcon = function (name) {
    return icons[name] || toolbarIcons[name] || '';
};
