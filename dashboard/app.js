/**
 * Afiliados AI Agent - Dashboard Frontend
 * Interactive dashboard for the affiliate marketing strategy.
 */

const API_BASE = '/api';
let charts = {};

// ─── Navigation ─────────────────────────────────────────────────────────────

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        item.classList.add('active');
        const view = document.getElementById(`view-${item.dataset.view}`);
        if (view) {
            view.classList.add('active');
            loadViewData(item.dataset.view);
        }
    });
});

function loadViewData(view) {
    switch (view) {
        case 'dashboard': loadDashboard(); break;
        case 'campaigns': loadCampaigns(); break;
        case 'groups': loadGroups(); break;
        case 'content': loadContent(); break;
        case 'leads': loadLeads(); break;
        case 'facebook': loadFacebookView(); break;
        case 'config': loadConfig(); break;
    }
}

// ─── API Helper ─────────────────────────────────────────────────────────────

async function api(path, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    return res.json();
}

// ─── Dashboard ──────────────────────────────────────────────────────────────

async function loadDashboard() {
    const data = await api('/dashboard/summary');
    document.getElementById('statCampaigns').textContent = data.active_campaigns_count || 0;
    document.getElementById('statGroups').textContent = data.total_groups || 0;
    document.getElementById('statContent').textContent = data.total_content || 0;
    document.getElementById('statLeads').textContent = data.total_leads || 0;

    // Lead Pipeline Chart
    const leads = data.leads || {};
    if (charts.leads) charts.leads.destroy();
    const ctxLeads = document.getElementById('leadsChart').getContext('2d');
    charts.leads = new Chart(ctxLeads, {
        type: 'doughnut',
        data: {
            labels: ['Nuevos', 'Contactados', 'Interesados', 'Cerrados', 'Perdidos'],
            datasets: [{
                data: [leads.new || 0, leads.contacted || 0, leads.interested || 0, leads.closed || 0, leads.lost || 0],
                backgroundColor: ['#0984e3', '#fdcb6e', '#00b894', '#6c5ce7', '#e17055'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#8b8d9a', padding: 12 } }
            }
        }
    });

    // Content Chart
    const content = data.content || {};
    if (charts.content) charts.content.destroy();
    const ctxContent = document.getElementById('contentChart').getContext('2d');
    charts.content = new Chart(ctxContent, {
        type: 'doughnut',
        data: {
            labels: ['Valor (80%)', 'Promoción (20%)'],
            datasets: [{
                data: [content.value || 0, content.promotion || 0],
                backgroundColor: ['#00b894', '#fdcb6e'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#8b8d9a', padding: 12 } }
            }
        }
    });

    // Groups Pipeline Chart
    const groups = data.groups || {};
    if (charts.groups) charts.groups.destroy();
    const ctxGroups = document.getElementById('groupsChart').getContext('2d');
    charts.groups = new Chart(ctxGroups, {
        type: 'bar',
        data: {
            labels: ['Descubiertos', 'Pendientes', 'En Prueba', 'Activos', 'Rechazados'],
            datasets: [{
                label: 'Grupos',
                data: [groups.discovered || 0, groups.pending_test || 0, groups.testing || 0, groups.active || 0, groups.rejected || 0],
                backgroundColor: ['#0984e3', '#fdcb6e', '#6c5ce7', '#00b894', '#e17055'],
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, ticks: { color: '#8b8d9a' } },
                x: { ticks: { color: '#8b8d9a' } }
            }
        }
    });
}

// ─── Campaigns ──────────────────────────────────────────────────────────────

async function loadCampaigns() {
    const campaigns = await api('/campaigns');
    const container = document.getElementById('campaignsTable');
    if (!campaigns || campaigns.length === 0) {
        container.innerHTML = `<p class="empty-state">📦 No hay campañas aún. ¡Crea tu primera campaña!</p>`;
        return;
    }
    let html = `<table>
        <thead><tr>
            <th>Nombre</th><th>Producto</th><th>Nicho</th><th>Estado</th><th>Ventas</th><th>Progreso</th><th>Acción</th>
        </tr></thead><tbody>`;
    for (const c of campaigns) {
        const progress = c.target_sales > 0 ? Math.round((c.current_sales / c.target_sales) * 100) : 0;
        const statusClass = {
            'draft': 'badge-neutral', 'setup': 'badge-info',
            'active': 'badge-success', 'completed': 'badge-info'
        }[c.status] || 'badge-neutral';
        html += `<tr>
            <td><strong>${c.name}</strong></td>
            <td>${c.product || '—'}</td>
            <td><span class="badge badge-info">${c.niche || '—'}</span></td>
            <td><span class="badge ${statusClass}">${c.status}</span></td>
            <td>${c.current_sales}/${c.target_sales}</td>
            <td>
                <div class="progress-bar"><div class="progress-fill" style="width:${progress}%"></div></div>
                <small style="color:var(--text-muted)">${progress}%</small>
            </td>
            <td><button class="btn btn-secondary" onclick="showCampaignDetail('${c.name}')">Ver</button></td>
        </tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function showNewCampaignModal() {
    const modal = document.getElementById('modalBody');
    modal.innerHTML = `
        <h2 style="margin-bottom:20px">➕ Nueva Campaña</h2>
        <form onsubmit="createCampaign(event)">
            <div class="form-group">
                <label>Nombre de la campaña</label>
                <input type="text" id="newCampName" required placeholder="Ej: Campaña Finanzas" />
            </div>
            <div class="form-group">
                <label>Producto a promocionar</label>
                <input type="text" id="newCampProduct" placeholder="Nombre del producto" />
            </div>
            <div class="form-group">
                <label>Nicho</label>
                <input type="text" id="newCampNiche" placeholder="Ej: finanzas, salud, marketing" />
            </div>
            <div class="form-group">
                <label>Meta de ventas</label>
                <input type="number" id="newCampTarget" value="10" />
            </div>
            <button type="submit" class="btn btn-primary">Crear Campaña</button>
        </form>
    `;
    document.getElementById('modalOverlay').classList.add('active');
}

async function createCampaign(e) {
    e.preventDefault();
    await api('/campaigns', 'POST', {
        name: document.getElementById('newCampName').value,
        product: document.getElementById('newCampProduct').value,
        niche: document.getElementById('newCampNiche').value,
        target_sales: parseInt(document.getElementById('newCampTarget').value),
    });
    closeModal();
    loadCampaigns();
}

// ─── Groups ─────────────────────────────────────────────────────────────────

async function loadGroups() {
    const groups = await api('/groups');
    const pipeline = await api('/groups/pipeline');

    // Pipeline
    const pipelineHtml = Object.entries(pipeline).map(([key, val]) => {
        if (key === 'total_prospects' || key === 'allows_promotion' || key === 'high_engagement') return '';
        const labels = {
            discovered: 'Descubiertos', pending_test: 'Pendientes',
            testing: 'En Prueba', active: 'Activos ✅', rejected: 'Rechazados ❌'
        };
        const colors = {
            discovered: 'var(--accent-blue)', pending_test: 'var(--accent-yellow)',
            testing: 'var(--accent)', active: 'var(--accent-green)', rejected: 'var(--accent-red)'
        };
        return `<div class="pipeline-item">
            <span class="number" style="color:${colors[key] || 'var(--text-primary)'}">${val}</span>
            <span class="label">${labels[key] || key}</span>
        </div>`;
    }).filter(Boolean).join('');
    document.getElementById('groupsPipeline').innerHTML = pipelineHtml || '<p>No hay grupos.</p>';

    // Table
    const container = document.getElementById('groupsTable');
    if (!groups || groups.length === 0) {
        container.innerHTML = `<p class="empty-state">🔍 No hay grupos registrados. Añade tu primer grupo.</p>`;
        return;
    }
    let html = `<table><thead><tr>
        <th>Nombre</th><th>Nicho</th><th>Miembros</th><th>Estado</th><th>Engagement</th><th>Acción</th>
    </tr></thead><tbody>`;
    for (const g of groups) {
        const statusClass = {
            discovered: 'badge-info', pending_test: 'badge-warning',
            testing: 'badge-neutral', active: 'badge-success', rejected: 'badge-danger'
        }[g.status] || 'badge-neutral';
        html += `<tr>
            <td><strong>${g.name}</strong></td>
            <td><span class="badge badge-info">${g.niche || '—'}</span></td>
            <td>${g.member_count || '—'}</td>
            <td><span class="badge ${statusClass}">${g.status}</span></td>
            <td>${g.engagement_score || '—'}</td>
            <td><button class="btn btn-secondary" onclick="updateGroupStatus('${g.name}')">Actualizar</button></td>
        </tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function showAddGroupModal() {
    const modal = document.getElementById('modalBody');
    modal.innerHTML = `
        <h2 style="margin-bottom:20px">🔍 Añadir Grupo Prospecto</h2>
        <form onsubmit="addGroup(event)">
            <div class="form-group">
                <label>Nombre del grupo de Facebook</label>
                <input type="text" id="newGroupName" required placeholder="Ej: Marketing Digital LATAM" />
            </div>
            <div class="form-group">
                <label>URL del grupo (opcional)</label>
                <input type="text" id="newGroupUrl" placeholder="https://facebook.com/groups/..." />
            </div>
            <div class="form-group">
                <label>Nicho</label>
                <input type="text" id="newGroupNiche" placeholder="Ej: marketing digital" />
            </div>
            <div class="form-group">
                <label>Miembros aproximados</label>
                <input type="number" id="newGroupMembers" value="0" />
            </div>
            <button type="submit" class="btn btn-primary">Añadir Grupo</button>
        </form>
    `;
    document.getElementById('modalOverlay').classList.add('active');
}

async function addGroup(e) {
    e.preventDefault();
    await api('/groups', 'POST', {
        name: document.getElementById('newGroupName').value,
        url: document.getElementById('newGroupUrl').value,
        niche: document.getElementById('newGroupNiche').value,
        member_count: parseInt(document.getElementById('newGroupMembers').value),
    });
    closeModal();
    loadGroups();
}

async function searchKeywords() {
    const niche = document.getElementById('nicheKeywords').value.trim();
    if (!niche) return;
    const data = await api(`/groups/keywords/${encodeURIComponent(niche)}`);
    const container = document.getElementById('keywordsResult');
    container.innerHTML = data.keywords.map(k => `<span class="keyword-tag">${k}</span>`).join('');
}

async function updateGroupStatus(name) {
    const newStatus = prompt(`Nuevo estado para "${name}"?\n1=Descubierto, 2=Pendiente, 3=En prueba, 4=Activo, 5=Rechazado`, '1');
    if (!newStatus) return;
    const statuses = {1:'discovered', 2:'pending_test', 3:'testing', 4:'active', 5:'rejected'};
    const status = statuses[parseInt(newStatus)];
    if (!status) return;
    // Actualizar estado via API PATCH
    await api(`/groups/${encodeURIComponent(name)}`, 'PATCH', { status });
    loadGroups();
}

// ─── Content ─────────────────────────────────────────────────────────────────

async function loadContent() {
    const stats = await api('/content/stats');
    const calendar = await api('/content/calendar');

    // Stats
    const compliance = stats.compliant ? '✅ CUMPLE' : '⚠️ NO CUMPLE';
    document.getElementById('contentStats').innerHTML = `
        <div class="pipeline-stats">
            <div class="pipeline-item">
                <span class="number" style="color:var(--accent-green)">${stats.value || 0}</span>
                <span class="label">Valor (80%)</span>
            </div>
            <div class="pipeline-item">
                <span class="number" style="color:var(--accent-yellow)">${stats.promotion || 0}</span>
                <span class="label">Promoción (20%)</span>
            </div>
            <div class="pipeline-item">
                <span class="number" style="color:var(--accent-blue)">${stats.total || 0}</span>
                <span class="label">Total Ideas</span>
            </div>
            <div class="pipeline-item">
                <span class="number" style="color:${stats.compliant ? 'var(--accent-green)' : 'var(--accent-red)'}">${(stats.ratio * 100).toFixed(0) || 0}%</span>
                <span class="label">Ratio Actual</span>
            </div>
        </div>
        <p style="margin-top:12px;font-size:0.9rem;color:var(--text-secondary)">
            Objetivo: 80% valor / 20% promoción — ${compliance}
        </p>
    `;

    // Calendar
    const dayNames = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
    const container = document.getElementById('contentCalendar');
    container.innerHTML = dayNames.map(day => {
        const items = calendar[day] || [];
        return `<div class="calendar-day">
            <div class="day-name">${day}</div>
            <div class="day-content">
                ${items.length ? items.map(i =>
                    `<div class="content-item ${i.content_type === 'value' ? 'idea-value' : 'idea-promo'}">
                        ${i.content_type === 'value' ? '📚' : '🛒'} ${i.title.substring(0, 40)}${i.title.length > 40 ? '...' : ''}
                    </div>`
                ).join('') : '<small style="color:var(--text-muted)">Sin contenido</small>'}
            </div>
        </div>`;
    }).join('');
}

async function generateIdeas() {
    const count = prompt('¿Cuántas ideas generar? (recomendado: 10)', '10');
    if (!count) return;
    const ideas = await api('/content/ideas', 'POST', { count: parseInt(count) });
    if (ideas && ideas.length > 0) {
        const valueCount = ideas.filter(i => i.content_type === 'value').length;
        const promoCount = ideas.filter(i => i.content_type === 'promotion').length;
        alert(`✅ ${ideas.length} ideas generadas!\n📚 Valor: ${valueCount}\n🛒 Promoción: ${promoCount}`);
        loadContent();
    }
}

// ─── Leads ───────────────────────────────────────────────────────────────────

async function loadLeads() {
    const leads = await api('/leads');
    const pipeline = await api('/leads/pipeline');

    // Pipeline
    const pipelineHtml = [
        { key: 'new', label: '🆕 Nuevos', color: 'var(--accent-blue)' },
        { key: 'contacted', label: '📞 Contactados', color: 'var(--accent-yellow)' },
        { key: 'interested', label: '🔥 Interesados', color: 'var(--accent-green)' },
        { key: 'closed', label: '✅ Cerrados', color: 'var(--accent)' },
        { key: 'lost', label: '❌ Perdidos', color: 'var(--accent-red)' },
    ].map(p => `
        <div class="pipeline-item">
            <span class="number" style="color:${p.color}">${pipeline[p.key] || 0}</span>
            <span class="label">${p.label}</span>
        </div>
    `).join('');
    document.getElementById('leadsPipeline').innerHTML = pipelineHtml;

    // Table
    const container = document.getElementById('leadsTable');
    if (!leads || leads.length === 0) {
        container.innerHTML = `<p class="empty-state">💬 No hay leads registrados. Captura tu primer lead.</p>`;
        return;
    }
    let html = `<table><thead><tr>
        <th>Nombre</th><th>WhatsApp</th><th>Fuente</th><th>Estado</th><th>Seguimientos</th><th>Acción</th>
    </tr></thead><tbody>`;
    for (const l of leads) {
        const statusBadge = {
            new: 'badge-info', contacted: 'badge-warning', meeting_set: 'badge-neutral',
            interested: 'badge-success', negotiation: 'badge-warning',
            closed: 'badge-success', lost: 'badge-danger'
        }[l.status] || 'badge-neutral';
        html += `<tr>
            <td><strong>${l.name}</strong></td>
            <td>${l.phone}</td>
            <td>${l.source_group || '—'}</td>
            <td><span class="badge ${statusBadge}">${l.status}</span></td>
            <td>${l.follow_up_count || 0}</td>
            <td>
                <button class="btn btn-secondary" onclick="updateLeadStatus('${l.phone}')">Actualizar</button>
            </td>
        </tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;
}

function showAddLeadModal() {
    const modal = document.getElementById('modalBody');
    modal.innerHTML = `
        <h2 style="margin-bottom:20px">💬 Nuevo Lead de WhatsApp</h2>
        <form onsubmit="addLead(event)">
            <div class="form-group">
                <label>Nombre del lead</label>
                <input type="text" id="newLeadName" required placeholder="Nombre completo" />
            </div>
            <div class="form-group">
                <label>WhatsApp (con código de país)</label>
                <input type="text" id="newLeadPhone" required placeholder="+584141234567" />
            </div>
            <div class="form-group">
                <label>Grupo de origen</label>
                <input type="text" id="newLeadSource" placeholder="¿De qué grupo llegó?" />
            </div>
            <div class="form-group">
                <label>Producto de interés</label>
                <input type="text" id="newLeadProduct" placeholder="¿Qué producto le interesa?" />
            </div>
            <button type="submit" class="btn btn-primary">Registrar Lead</button>
        </form>
    `;
    document.getElementById('modalOverlay').classList.add('active');
}

async function addLead(e) {
    e.preventDefault();
    await api('/leads', 'POST', {
        name: document.getElementById('newLeadName').value,
        phone: document.getElementById('newLeadPhone').value,
        source_group: document.getElementById('newLeadSource').value,
        product_interest: document.getElementById('newLeadProduct').value,
    });
    closeModal();
    loadLeads();
}

function showWalingModal() {
    const modal = document.getElementById('modalBody');
    modal.innerHTML = `
        <h2 style="margin-bottom:20px">🔗 Genera tu enlace wa.link</h2>
        <form onsubmit="generateWaling(event)">
            <div class="form-group">
                <label>Tu número de WhatsApp (con código de país)</label>
                <input type="text" id="walingPhone" required placeholder="+584141234567" />
            </div>
            <button type="submit" class="btn btn-primary">Generar Enlace</button>
        </form>
        <div id="walingResult" style="margin-top:16px"></div>
    `;
    document.getElementById('modalOverlay').classList.add('active');
}

async function generateWaling(e) {
    e.preventDefault();
    const phone = document.getElementById('walingPhone').value.replace(/[^0-9]/g, '');
    const waMe = `https://wa.me/${phone}`;
    document.getElementById('walingResult').innerHTML = `
        <div class="card">
            <p style="word-break:break-all;color:var(--accent-light);font-size:1.1rem">🔗 <a href="${waMe}" target="_blank" style="color:var(--accent-light)">${waMe}</a></p>
            <p style="color:var(--text-secondary);font-size:0.85rem;margin-top:8px">
                💡 Pon este enlace en tu biografía y publicaciones promocionales<br>
                <small>También puedes acortarlo con: <a href="https://wa.link" target="_blank" style="color:var(--accent)">wa.link</a></small>
            </p>
        </div>
    `;
}

async function updateLeadStatus(phone) {
    const statuses = ['new', 'contacted', 'meeting_set', 'interested', 'negotiation', 'closed', 'lost'];
    const current = prompt(`Nuevo estado para ${phone}?\n1=Nuevo, 2=Contactado, 3=Reunión, 4=Interesado, 5=Negociación, 6=Cerrado ✅, 7=Perdido ❌`, '1');
    if (!current) return;
    const status = statuses[parseInt(current) - 1];
    if (!status) return;
    await api(`/leads/${encodeURIComponent(phone)}`, 'PATCH', { status });
    loadLeads();
}

// ─── Knowledge Base ─────────────────────────────────────────────────────────

async function showKnowledge(type) {
    const modal = document.getElementById('modalBody');
    let title, content;

    switch (type) {
        case 'sales': {
            const data = await api('/knowledge/sales-psychology');
            title = '🧠 Psicología de Venta';
            content = data.tips.map((t, i) => `<li>${i+1}. ${t}</li>`).join('');
            break;
        }
        case 'content': {
            const data = await api('/knowledge/value-content');
            title = '📚 Tipos de Contenido de Valor';
            content = data.types.map(t =>
                `<li><strong>${t.tipo}</strong> — ${t.ejemplo} <small style="color:var(--text-muted)">(${t.formato})</small></li>`
            ).join('');
            break;
        }
        case 'niches': {
            const data = await api('/knowledge/niches');
            title = '🏆 Nichos Rentables';
            content = data.niches.map(n =>
                `<li>${n.nivel} <strong>${n.nombre}</strong>: ${n.descripcion}</li>`
            ).join('');
            break;
        }
        case 'script': {
            const data = await api('/knowledge/whatsapp-script');
            title = '📖 Guión de WhatsApp';
            content = `
                <h3>💬 Saludo Inicial</h3>
                <li>${data.saludo_inicial}</li>
                <h3>🔍 Descubrimiento</h3>
                <li>${data.descubrimiento}</li>
                <h3>🎯 Presentación de Valor</h3>
                <li>${data.presentacion_valor}</li>
                <h3>❓ Manejo de Objeciones</h3>
                ${Object.entries(data.manejo_objecciones || {}).map(([k,v]) => `<li><strong>${k}:</strong> ${v}</li>`).join('')}
                <h3>🏁 Cierre</h3>
                <li>${data.cierre}</li>
            `;
            break;
        }
        case 'warmup': {
            const data = { tips: [
                'Los primeros 3 días: solo comenta en posts existentes, no publiques',
                'Día 4-7: publica 1 post de valor (sin promocionar nada)',
                'Día 8-10: publica otro post de valor y comenta en otros posts',
                'Día 11+: si el grupo lo permite, publica tu primer post promocional',
                'Sé auténtico. La gente detecta cuando eres un bot o un spammer.'
            ]};
            title = '🌡️ Warm Up para Grupos';
            content = data.tips.map(t => `<li>${t}</li>`).join('');
            break;
        }
        case 'metrics': {
            const data = await api('/knowledge/metrics');
            title = '📈 Métricas Clave';
            content = data.metrics.map(m =>
                `<li><strong>${m.metrica}</strong>: ${m.porque}</li>`
            ).join('');
            break;
        }
        default: return;
    }

    modal.innerHTML = `
        <div class="knowledge-detail">
            <h2>${title}</h2>
            <ul>${content}</ul>
        </div>
    `;
    document.getElementById('modalOverlay').classList.add('active');
}

// ─── Facebook Poster ───────────────────────────────────────────────────────

async function loadFacebookView() {
    try {
        const data = await api('/facebook/status');
        const status = data.status || {};
        const stats = data.stats || {};
        const config = data.config || {};

        // Stats cards
        document.getElementById('fbPostsToday').textContent = status.posts_today || 0;
        document.getElementById('fbSuccess').textContent = stats.total_success || 0;
        document.getElementById('fbFailures').textContent = stats.total_failures || 0;
        document.getElementById('fbRate').textContent = (stats.success_rate || 0) + '%';

        // Config
        document.getElementById('fbEnabled').checked = config.enabled || false;
        document.getElementById('fbMaxPosts').value = config.max_posts_per_day || 5;
        document.getElementById('fbPostBtn').disabled = !config.enabled;

        // Profile status
        const profileDiv = document.getElementById('fbProfileStatus');
        if (status.profile_exists) {
            profileDiv.innerHTML = `
                <div class="pipeline-stats">
                    <div class="pipeline-item">
                        <span class="number" style="color:var(--accent-green)">✅</span>
                        <span class="label">Perfil existe</span>
                    </div>
                    <div class="pipeline-item">
                        <span class="number" style="color:${status.cookies_exist ? 'var(--accent-green)' : 'var(--accent-red)'}">
                            ${status.cookies_exist ? '✅' : '❌'}
                        </span>
                        <span class="label">Cookies</span>
                    </div>
                    <div class="pipeline-item">
                        <span class="number" style="color:var(--accent-blue)">${status.remaining_today}</span>
                        <span class="label">Posts disponibles hoy</span>
                    </div>
                </div>
                <p style="margin-top:8px;font-size:0.8rem;color:var(--text-muted)">
                    Perfil: ${status.profile_path}
                </p>
            `;
        } else {
            profileDiv.innerHTML = `
                <div class="pipeline-stats">
                    <div class="pipeline-item">
                        <span class="number" style="color:var(--accent-red)">❌</span>
                        <span class="label">Perfil no configurado</span>
                    </div>
                </div>
                <p style="margin-top:8px;color:var(--accent-yellow)">
                    💡 Haz clic en "Configurar Perfil Chrome" para iniciar sesión en Facebook manualmente.
                </p>
            `;
        }

        // Post log
        loadFbPostLog();
    } catch (e) {
        console.error('Error loading Facebook view:', e);
    }
}

async function loadFbPostLog() {
    try {
        const data = await api('/facebook/post-log');
        const posts = data.posts || [];
        const container = document.getElementById('fbPostLog');

        if (posts.length === 0) {
            container.innerHTML = `<p class="empty-state">📝 No hay publicaciones registradas aún.</p>`;
            return;
        }

        let html = `<table><thead><tr>
            <th>Grupo</th><th>Contenido</th><th>Estado</th><th>Hora</th><th>Duración</th>
        </tr></thead><tbody>`;

        for (const p of posts.slice().reverse()) {
            const statusBadge = p.success ? 'badge-success' : 'badge-danger';
            const statusText = p.success ? '✅ Éxito' : '❌ Fallo';
            const errorInfo = p.error ? `<small style="color:var(--accent-red)">${p.error}</small>` : '';
            const time = p.timestamp ? new Date(p.timestamp).toLocaleTimeString() : '—';
            const duration = p.duration_seconds ? `${p.duration_seconds.toFixed(0)}s` : '—';

            html += `<tr>
                <td><strong>${p.group_name}</strong></td>
                <td>${p.content_title ? p.content_title.substring(0, 40) + (p.content_title.length > 40 ? '...' : '') : '—'}</td>
                <td><span class="badge ${statusBadge}">${statusText}</span><br>${errorInfo}</td>
                <td>${time}</td>
                <td>${duration}</td>
            </tr>`;
        }
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (e) {
        console.error('Error loading FB post log:', e);
    }
}

async function toggleFacebook() {
    const enabled = document.getElementById('fbEnabled').checked;
    await api('/facebook/config', 'POST', { enabled });
    document.getElementById('fbPostBtn').disabled = !enabled;
    loadFacebookView();
}

async function saveFbConfig() {
    const enabled = document.getElementById('fbEnabled').checked;
    const maxPosts = parseInt(document.getElementById('fbMaxPosts').value);
    await api('/facebook/config', 'POST', { enabled, max_posts_per_day: maxPosts });
    alert('✅ Configuración guardada');
    loadFacebookView();
}

async function fbSetupProfile() {
    if (!confirm('⚠️ Se abrirá una ventana de Chrome.\n\n1. Inicia sesión en Facebook MANUALMENTE\n2. Espera a que la página cargue tu feed\n3. Vuelve a este dashboard\n\n¿Continuar?')) return;
    
    const msg = document.getElementById('fbProfileStatus');
    msg.innerHTML = `<p style="text-align:center;color:var(--accent-yellow)">⏳ Abriendo Chrome para configuración...<br><small>Espera a que se abra la ventana de Chrome</small></p>`;
    
    // La configuración del perfil abre Chrome - notificamos al usuario
    alert('🔧 Chrome se abrirá en una ventana separada.\n\nINSTRUCCIONES:\n1. Inicia sesión en Facebook\n2. Si ves tu feed, la configuración fue exitosa\n3. Cierra Chrome y presiona OK aquí\n\nPara ejecutar manualmente: python run.py --fb-setup');
    
    loadFacebookView();
}

async function fbPostNow() {
    if (!confirm('🚀 ¿Publicar ahora en grupos activos?\n\nSe abrirá Chrome y comenzará a publicar automáticamente.')) return;
    
    const maxPosts = parseInt(document.getElementById('fbMaxPosts').value);
    const container = document.getElementById('fbPostLog');
    container.innerHTML = `<p style="text-align:center;color:var(--accent-yellow)">⏳ Publicando... (esto puede tomar varios minutos)</p>`;
    
    try {
        const result = await api('/facebook/post', 'POST', { max_posts: maxPosts });
        if (result.success) {
            const summary = result.summary;
            alert(`✅ Publicación completada:\nExitosas: ${summary.successful}\nFallidas: ${summary.failed}`);
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (e) {
        alert(`❌ Error: ${e.message}`);
    }
    
    loadFacebookView();
}

// ─── Config ─────────────────────────────────────────────────────────────────

async function loadConfig() {
    const config = await api('/config');
    document.getElementById('configNiche').value = config.niche || '';
    document.getElementById('configFanPage').value = config.fan_page_name || '';
    document.getElementById('configWhatsapp').value = config.whatsapp_number || '';
}

async function saveConfig(e) {
    e.preventDefault();
    await api('/config', 'POST', {
        niche: document.getElementById('configNiche').value,
        fan_page_name: document.getElementById('configFanPage').value,
        whatsapp_number: document.getElementById('configWhatsapp').value,
    });
    alert('✅ Configuración guardada exitosamente');
}

// ─── Modal ──────────────────────────────────────────────────────────────────

function closeModal(e) {
    if (e && e.target !== document.getElementById('modalOverlay') && e.target.closest('.modal')) return;
    document.getElementById('modalOverlay').classList.remove('active');
}

// ─── Initial Load ───────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadConfig();
});
