// On-screen controls for the chalkboard plugin from reveal.js-plugins, which
// does the drawing. That plugin ships keyboard bindings only (C, B, DEL), so a
// touch screen or a tablet has no way in. This adds a toolbar of finger-sized
// buttons:
//
//   pen         draw on the current slide (same as C)
//   whiteboard  open a blank whiteboard over the slide (same as B)
//   clear       wipe the drawing on whichever layer is open (same as DEL)
//   fullscreen  put the browser in fullscreen, so the whiteboard gets the
//               whole screen. Hidden where the browser cannot do it (iPhone).
//
// A chevron at the left end collapses the toolbar to that one button, so it
// stays off the slides. It starts collapsed, remembers the choice per browser,
// and opens by itself when C or B starts a drawing, so clear is in reach.
//
// Load order: this file and chalkboard/plugin.js are classic scripts, loaded
// before Reveal.initialize. Pass both plugins, chalkboard first:
//
//   chalkboard: RevealWhiteboard.config(),
//   plugins: [RevealChalkboard, RevealWhiteboard],
//
// Images: the chalkboard plugin finds its pen cursors and board texture next
// to its own <script src>. The single file build has no src, so build.mjs sets
// window.WHITEBOARD_IMG to a map of file name -> data URI first. When that is
// absent, the images load from the vendored package.

(() => {
  const BASE = 'lib/node_modules/reveal.js-plugins/chalkboard/img/';
  const img = (name) => (window.WHITEBOARD_IMG ? window.WHITEBOARD_IMG[name] : BASE + name);

  // Red first: the slides are dark and the whiteboard is white, and the first
  // pen is what you get on opening either. The plugin's own default is grey,
  // which disappears on these slides.
  const PENS = [
    ['rgba(232,69,60,1)', 'red'],
    ['rgba(30,144,255,1)', 'blue'],
    ['rgba(50,205,50,1)', 'green'],
    ['rgba(255,140,0,1)', 'orange'],
    ['rgba(255,220,0,1)', 'yellow'],
    ['rgba(40,40,40,1)', 'black'],
  ];

  function config() {
    const pens = PENS.map(([color, cursor]) => ({
      color,
      cursor: `url(${img(`boardmarker-${cursor}.png`)}), auto`,
    }));
    return {
      theme: 'whiteboard',
      // Both lists set to the same pens. In whiteboard mode the plugin draws
      // with `boardmarkers` but builds the board's colour palette from
      // `chalks`, so they must match or the swatches lie.
      boardmarkers: pens,
      chalks: pens,
      background: ['rgba(127,127,127,.1)', img('whiteboard.png')],
      eraser: { src: img('sponge.png'), radius: 24 },
      boardmarkerWidth: 4,
      // Extra boards per slide need Font Awesome chevrons, which this deck
      // does not ship. One board per slide is plenty for a workshop.
      boardHandle: false,
      transition: 400,
    };
  }

  const ICONS = {
    pen: '<path d="M4 20h4L19 9l-4-4L4 16v4z"/><path d="M13.5 6.5l4 4"/>',
    board: '<rect x="3" y="4" width="18" height="13" rx="1.5"/><path d="M8 21l4-4 4 4"/>',
    clear: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    enter: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    exit: '<path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5"/>',
    open: '<path d="M9 6l6 6-6 6"/>',
    close: '<path d="M15 6l-6 6 6 6"/>',
  };
  const svg = (name) =>
    `<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" ` +
    `stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[name]}</svg>`;

  const doc = document;
  const fsElement = () => doc.fullscreenElement || doc.webkitFullscreenElement;
  const fsSupported = () => !!(doc.fullscreenEnabled || doc.webkitFullscreenEnabled);
  function toggleFullscreen() {
    if (fsElement()) {
      (doc.exitFullscreen || doc.webkitExitFullscreen).call(doc);
    } else {
      const el = doc.documentElement;
      (el.requestFullscreen || el.webkitRequestFullscreen).call(el);
    }
  }

  function init(deck) {
    const board = window.RevealChalkboard;
    if (!board || !board.toggleChalkboard) {
      console.error('RevealWhiteboard: load RevealChalkboard before it in plugins.');
      return;
    }

    const bar = doc.createElement('div');
    bar.className = 'wb-toolbar';
    bar.setAttribute('role', 'toolbar');
    bar.setAttribute('aria-label', 'Whiteboard');
    // Taps on the toolbar must not turn into a slide swipe.
    bar.setAttribute('data-prevent-swipe', '');

    const button = (name, label, action) => {
      const b = doc.createElement('button');
      b.type = 'button';
      b.className = `wb-btn wb-${name}`;
      b.title = label;
      b.setAttribute('aria-label', label);
      b.innerHTML = svg(name);
      // pointerup covers mouse, pen and finger alike. Taking it here, and
      // swallowing the click that follows, keeps a tap from firing twice.
      b.addEventListener('pointerup', (e) => {
        e.preventDefault();
        e.stopPropagation();
        action();
        sync();
      });
      b.addEventListener('click', (e) => e.preventDefault());
      bar.appendChild(b);
      return b;
    };

    // Collapsed by default. localStorage can throw (private mode, blocked
    // storage), and the toolbar must work without it.
    const KEY = 'wb-collapsed';
    let collapsed = true;
    try { collapsed = localStorage.getItem(KEY) !== '0'; } catch {}
    function setCollapsed(value, remember) {
      collapsed = value;
      bar.classList.toggle('wb-collapsed', collapsed);
      toggleBtn.innerHTML = svg(collapsed ? 'open' : 'close');
      toggleBtn.title = collapsed ? 'Show drawing tools' : 'Hide drawing tools';
      toggleBtn.setAttribute('aria-label', toggleBtn.title);
      toggleBtn.setAttribute('aria-expanded', !collapsed);
      if (remember) try { localStorage.setItem(KEY, collapsed ? '1' : '0'); } catch {}
    }
    const toggleBtn = button('toggle', '', () => setCollapsed(!collapsed, true));
    toggleBtn.classList.add('wb-toggle');

    const penBtn = button('pen', 'Draw on slide (C)', () => board.toggleNotesCanvas());
    const boardBtn = button('board', 'Whiteboard (B)', () => board.toggleChalkboard());
    const clearBtn = button('clear', 'Clear drawing (Delete)', () => board.clear());
    const fsBtn = button('enter', 'Fullscreen (F)', toggleFullscreen);
    if (!fsSupported()) fsBtn.hidden = true;

    // The plugin keeps its state private. Read it back off its two layers,
    // which it shows and hides through inline styles.
    const notesLayer = () => doc.getElementById('notescanvas');
    const boardLayer = () => doc.getElementById('chalkboard');
    function sync() {
      const n = notesLayer();
      const c = boardLayer();
      const boardOn = !!c && c.style.visibility === 'visible';
      const penOn = !boardOn && !!n && n.style.pointerEvents === 'auto';
      penBtn.setAttribute('aria-pressed', penOn);
      boardBtn.setAttribute('aria-pressed', boardOn);
      clearBtn.disabled = !(penOn || boardOn);
      const fs = !!fsElement();
      fsBtn.setAttribute('aria-pressed', fs);
      fsBtn.innerHTML = svg(fs ? 'exit' : 'enter');
      fsBtn.title = fs ? 'Exit fullscreen (F)' : 'Fullscreen (F)';
      fsBtn.setAttribute('aria-label', fsBtn.title);
      bar.classList.toggle('wb-active', penOn || boardOn);
      // A keyboard shortcut opened a layer while collapsed: show the tools.
      // Only on the moment it opens, so collapsing mid-drawing still works.
      const active = penOn || boardOn;
      if (active && !wasActive && collapsed) setCollapsed(false, false);
      wasActive = active;
      // The board forgets its pen on every opening and starts on the first
      // one (rememberColor), so the swatch has to follow it back.
      if (boardOn && !wasBoardOn) markSwatch(c && c.querySelector('.palette li'));
      wasBoardOn = boardOn;
    }
    let wasBoardOn = false;
    let wasActive = false;

    // On a touch screen there is no cursor to show which pen is live, so ring
    // the chosen swatch instead.
    function markSwatch(li) {
      if (!li) return;
      for (const other of li.parentElement.children) other.classList.remove('wb-selected');
      li.classList.add('wb-selected');
    }

    // Keyboard shortcuts change the layers behind our back, so watch them.
    const watch = new MutationObserver(sync);
    deck.on('ready', () => {
      for (const layer of [notesLayer(), boardLayer()]) {
        if (!layer) continue;
        watch.observe(layer, { attributes: true, attributeFilter: ['style'] });
        const palette = layer.querySelector('.palette');
        if (!palette) continue;
        markSwatch(palette.querySelector('li'));
        palette.addEventListener('pointerdown', (e) => markSwatch(e.target.closest('li')));
      }
      sync();
    });
    doc.addEventListener('fullscreenchange', sync);
    doc.addEventListener('webkitfullscreenchange', sync);

    setCollapsed(collapsed, false);
    deck.getRevealElement().appendChild(bar);
    sync();
  }

  window.RevealWhiteboard = { id: 'whiteboard', init, config };
})();
