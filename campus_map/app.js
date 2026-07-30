document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const buildingListEl = document.getElementById('buildingList');
  const searchInput = document.getElementById('searchInput');
  const filterChips = document.querySelectorAll('.filter-chip');
  const locationCountEl = document.getElementById('locationCount');
  
  const routeStartSelect = document.getElementById('routeStart');
  const routeEndSelect = document.getElementById('routeEnd');
  const routeInfoEl = document.getElementById('routeInfo');
  const routeTimeEl = document.getElementById('routeTime');
  const routeDistEl = document.getElementById('routeDist');
  const clearRouteBtn = document.getElementById('clearRouteBtn');
  
  const svgPinsGroup = document.getElementById('svgPinsGroup');
  const routePolyline = document.getElementById('routePolyline');
  
  // Modal Elements
  const detailModal = document.getElementById('detailModal');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const modalCategoryBadge = document.getElementById('modalCategoryBadge');
  const modalTitle = document.getElementById('modalTitle');
  const modalTagline = document.getElementById('modalTagline');
  const modalVisualCard = document.getElementById('modalVisualCard');
  const modalHours = document.getElementById('modalHours');
  const modalFacilities = document.getElementById('modalFacilities');
  const modalDescription = document.getElementById('modalDescription');
  const modalSetStartBtn = document.getElementById('modalSetStartBtn');
  const modalSetEndBtn = document.getElementById('modalSetEndBtn');
  const modalGmapsBtn = document.getElementById('modalGmapsBtn');
  
  const themeToggle = document.getElementById('themeToggle');

  // State
  let currentCategory = 'all';
  let searchQuery = '';
  let selectedBuilding = null;

  // Initialize
  initPopulateSelects();
  renderBuildingsList();
  filterSvgNodes();
  setupEventListeners();

  // Populate Route Dropdowns
  function initPopulateSelects() {
    routeStartSelect.innerHTML = '<option value="">Choose Start Location...</option>';
    routeEndSelect.innerHTML = '<option value="">Choose Destination...</option>';

    CAMPUS_BUILDINGS.forEach(b => {
      const opt1 = document.createElement('option');
      opt1.value = b.id;
      opt1.textContent = `${b.icon} ${b.name}`;
      routeStartSelect.appendChild(opt1);

      const opt2 = document.createElement('option');
      opt2.value = b.id;
      opt2.textContent = `${b.icon} ${b.name}`;
      routeEndSelect.appendChild(opt2);
    });
  }

  // Render Sidebar Building Cards
  function renderBuildingsList() {
    const filtered = CAMPUS_BUILDINGS.filter(b => {
      const matchesCat = currentCategory === 'all' || b.category === currentCategory;
      const matchesSearch = b.name.toLowerCase().includes(searchQuery) ||
                            b.desc.toLowerCase().includes(searchQuery) ||
                            b.tagline.toLowerCase().includes(searchQuery);
      return matchesCat && matchesSearch;
    });

    locationCountEl.textContent = filtered.length;
    buildingListEl.innerHTML = '';

    if (filtered.length === 0) {
      buildingListEl.innerHTML = `
        <div class="empty-state" style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px;">
          No places found matching "${searchQuery}"
        </div>`;
      return;
    }

    filtered.forEach(b => {
      const card = document.createElement('div');
      card.className = `building-card ${selectedBuilding?.id === b.id ? 'active' : ''}`;
      card.dataset.id = b.id;

      card.innerHTML = `
        <div class="card-icon-wrapper">${b.icon}</div>
        <div class="card-content">
          <div class="card-top">
            <span class="card-title">${b.name}</span>
            <span class="card-badge ${b.category}">${b.catLabel}</span>
          </div>
          <p class="card-sub">${b.tagline}</p>
        </div>
      `;

      card.addEventListener('click', () => {
        selectBuilding(b.id);
        openBuildingModal(b);
      });

      buildingListEl.appendChild(card);
    });
  }

  // Filter SVG Map Nodes according to active Category Chip
  function filterSvgNodes() {
    document.querySelectorAll('.building-node').forEach(node => {
      const bId = node.dataset.id;
      const b = CAMPUS_BUILDINGS.find(item => item.id === bId);
      if (!b) return;

      const matchesCat = currentCategory === 'all' || b.category === currentCategory;
      const matchesSearch = b.name.toLowerCase().includes(searchQuery);

      if (matchesCat && matchesSearch) {
        node.style.opacity = '1';
        node.style.pointerEvents = 'auto';
      } else {
        node.style.opacity = '0.25';
        node.style.pointerEvents = 'none';
      }
    });
  }

  // Select building on map and scroll sidebar card into view
  function selectBuilding(id) {
    selectedBuilding = CAMPUS_BUILDINGS.find(b => b.id === id);
    
    // Highlight SVG Node
    document.querySelectorAll('.building-node').forEach(node => {
      node.classList.toggle('active', node.dataset.id === id);
    });
    document.querySelectorAll('.building-card').forEach(card => {
      card.classList.toggle('active', card.dataset.id === id);
    });
  }

  // Generate Realistic Building / Food Stall Preview HTML for Modal
  function getBuildingVisualHTML(b) {
    if (b.id === 'mayuri_ab') {
      return `
        <div class="visual-food-card">
          <div class="food-title">🍛 Mayuri Canteen (AB1 Side)</div>
          <div class="food-menu-items">
            <span class="item-tag">Daily Thali</span>
            <span class="item-tag">Paneer Butter Masala</span>
            <span class="item-tag">Samosa & Tea</span>
            <span class="item-tag">Aloo Paratha</span>
          </div>
        </div>
      `;
    } else if (b.id === 'ub_ab') {
      return `
        <div class="visual-food-card" style="background: #f0fdf4; border-color: #bbf7d0;">
          <div class="food-title" style="color: #15803d;">🌳 Under the Tree (UB Cafe)</div>
          <div class="food-menu-items">
            <span class="item-tag" style="color: #166534; border-color: #86efac;">Special Chai</span>
            <span class="item-tag" style="color: #166534; border-color: #86efac;">Cheese Maggi</span>
            <span class="item-tag" style="color: #166534; border-color: #86efac;">Aloo Patties</span>
            <span class="item-tag" style="color: #166534; border-color: #86efac;">Cold Coffee</span>
          </div>
        </div>
      `;
    } else if (b.id === 'ab_dakshin') {
      return `
        <div class="visual-food-card" style="background: #fefce8; border-color: #fef08a;">
          <div class="food-title" style="color: #a16207;">🥟 AB Dakshin (South Indian)</div>
          <div class="food-menu-items">
            <span class="item-tag" style="color: #854d0e; border-color: #fde047;">Masala Dosa</span>
            <span class="item-tag" style="color: #854d0e; border-color: #fde047;">Idli Sambhar</span>
            <span class="item-tag" style="color: #854d0e; border-color: #fde047;">Filter Coffee</span>
            <span class="item-tag" style="color: #854d0e; border-color: #fde047;">Onion Uttapam</span>
          </div>
        </div>
      `;
    } else if (b.id === 'bistro') {
      return `
        <div class="visual-food-card" style="background: #fffbeb; border-color: #fde68a;">
          <div class="food-title" style="color: #d97706;">🍕 The Bistro</div>
          <div class="food-menu-items">
            <span class="item-tag">Farmhouse Pizza</span>
            <span class="item-tag">White Sauce Pasta</span>
            <span class="item-tag">Crispy Burger</span>
            <span class="item-tag">Oreo Shake</span>
          </div>
        </div>
      `;
    } else if (b.id === 'mayuri_ab2') {
      return `
        <div class="visual-food-card">
          <div class="food-title">🍱 Mayuri Eatery (AB2 Side)</div>
          <div class="food-menu-items">
            <span class="item-tag">Kathi Rolls</span>
            <span class="item-tag">Fresh Fruit Juices</span>
            <span class="item-tag">Sandwiches</span>
            <span class="item-tag">Hot Coffee</span>
          </div>
        </div>
      `;
    } else if (b.id === 'ab1') {
      return `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center;">
          <div style="font-weight: 800; font-size: 16px; color: #1c1f26; font-family: 'Outfit', sans-serif;">🏛️ Academic Block 1 (AB1)</div>
          <p style="font-size: 12px; color: #64748b; margin-top: 4px;">Main Auditorium • Deans' Offices • Smart Classrooms</p>
        </div>
      `;
    } else {
      return `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center;">
          <div style="font-size: 24px; margin-bottom: 4px;">${b.icon}</div>
          <div style="font-weight: 800; font-size: 15px; color: #1c1f26; font-family: 'Outfit', sans-serif;">${b.name}</div>
        </div>
      `;
    }
  }

  // Open Modal
  function openBuildingModal(b) {
    modalCategoryBadge.textContent = b.catLabel;
    modalCategoryBadge.className = `badge ${b.category}`;
    modalTitle.textContent = b.name;
    modalTagline.textContent = b.tagline;
    modalHours.textContent = b.hours;
    modalFacilities.textContent = b.facilities;
    modalDescription.textContent = b.desc;
    
    modalVisualCard.innerHTML = getBuildingVisualHTML(b);

    const query = encodeURIComponent(`${b.gmapsQuery}`);
    modalGmapsBtn.href = `https://www.google.com/maps/search/?api=1&query=${query}`;

    detailModal.classList.remove('hidden');
  }

  // Close Modal
  closeModalBtn.addEventListener('click', () => {
    detailModal.classList.add('hidden');
  });
  detailModal.addEventListener('click', (e) => {
    if (e.target === detailModal) detailModal.classList.add('hidden');
  });

  // Setup Event Listeners
  function setupEventListeners() {
    // Search input
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderBuildingsList();
      filterSvgNodes();
    });

    // Category Filter Chips
    filterChips.forEach(chip => {
      chip.addEventListener('click', () => {
        filterChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        currentCategory = chip.dataset.cat;
        renderBuildingsList();
        filterSvgNodes();
      });
    });

    // Keyboard '/' shortcut
    window.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput.focus();
      }
    });

    // Modal Set Start / End Route Buttons
    modalSetStartBtn.addEventListener('click', () => {
      if (selectedBuilding) {
        routeStartSelect.value = selectedBuilding.id;
        calculateAndDrawRoute();
        detailModal.classList.add('hidden');
      }
    });

    modalSetEndBtn.addEventListener('click', () => {
      if (selectedBuilding) {
        routeEndSelect.value = selectedBuilding.id;
        calculateAndDrawRoute();
        detailModal.classList.add('hidden');
      }
    });

    // Route Pathfinder Selects
    routeStartSelect.addEventListener('change', calculateAndDrawRoute);
    routeEndSelect.addEventListener('change', calculateAndDrawRoute);
    clearRouteBtn.addEventListener('click', clearRoute);

    // SVG Building Node Clicks
    document.querySelectorAll('.building-node').forEach(node => {
      node.addEventListener('click', (e) => {
        e.stopPropagation();
        const bId = node.dataset.id;
        const b = CAMPUS_BUILDINGS.find(item => item.id === bId);
        if (b) {
          selectBuilding(bId);
          openBuildingModal(b);
        }
      });
    });

    // Zoom Controls
    let scale = 1;
    const mapWrapper = document.getElementById('mapWrapper');
    document.getElementById('zoomInBtn').addEventListener('click', () => {
      scale = Math.min(scale + 0.2, 2.2);
      mapWrapper.style.transform = `scale(${scale})`;
    });
    document.getElementById('zoomOutBtn').addEventListener('click', () => {
      scale = Math.max(scale - 0.2, 0.8);
      mapWrapper.style.transform = `scale(${scale})`;
    });
    document.getElementById('resetMapBtn').addEventListener('click', () => {
      scale = 1;
      mapWrapper.style.transform = `scale(1)`;
    });

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-theme');
      const isDark = document.body.classList.contains('dark-theme');
      themeToggle.querySelector('.theme-icon').textContent = isDark ? '🌙' : '☀️';
    });
  }

  function clearRoute() {
    routeStartSelect.value = '';
    routeEndSelect.value = '';
    routePolyline.setAttribute('d', '');
    routeInfoEl.classList.add('hidden');
  }

  // Shortest Path Graph Algorithm (Dijkstra)
  function calculateAndDrawRoute() {
    const startId = routeStartSelect.value;
    const endId = routeEndSelect.value;

    if (!startId || !endId || startId === endId) {
      routePolyline.setAttribute('d', '');
      routeInfoEl.classList.add('hidden');
      return;
    }

    const path = findShortestPath(startId, endId);
    if (path && path.length > 1) {
      let pathD = '';
      let totalDist = 0;

      for (let i = 0; i < path.length; i++) {
        const node = CAMPUS_GRAPH.nodes[path[i]];
        if (i === 0) {
          pathD += `M ${node.x} ${node.y}`;
        } else {
          pathD += ` L ${node.x} ${node.y}`;
          const prevNode = CAMPUS_GRAPH.nodes[path[i - 1]];
          const dx = node.x - prevNode.x;
          const dy = node.y - prevNode.y;
          totalDist += Math.sqrt(dx * dx + dy * dy);
        }
      }

      routePolyline.setAttribute('d', pathD);
      
      const meters = Math.round(totalDist * 1.8);
      const walkTime = Math.max(1, Math.round(meters / 80));

      routeDistEl.textContent = `${meters} m`;
      routeTimeEl.textContent = `${walkTime} min`;
      routeInfoEl.classList.remove('hidden');
    }
  }

  function findShortestPath(start, end) {
    const distances = {};
    const previous = {};
    const nodes = new Set(Object.keys(CAMPUS_GRAPH.nodes));

    nodes.forEach(node => {
      distances[node] = Infinity;
      previous[node] = null;
    });

    distances[start] = 0;

    while (nodes.size > 0) {
      let smallest = null;
      nodes.forEach(node => {
        if (smallest === null || distances[node] < distances[smallest]) {
          smallest = node;
        }
      });

      if (smallest === end || distances[smallest] === Infinity) {
        break;
      }

      nodes.delete(smallest);

      CAMPUS_GRAPH.edges.forEach(edge => {
        let neighbor = null;
        if (edge.from === smallest) neighbor = edge.to;
        if (edge.to === smallest) neighbor = edge.from;

        if (neighbor && nodes.has(neighbor)) {
          const alt = distances[smallest] + edge.dist;
          if (alt < distances[neighbor]) {
            distances[neighbor] = alt;
            previous[neighbor] = smallest;
          }
        }
      });
    }

    const path = [];
    let curr = end;
    while (curr) {
      path.unshift(curr);
      curr = previous[curr];
    }
    return path.length > 1 ? path : null;
  }
});
