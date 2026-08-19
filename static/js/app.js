// Global State Variables
let currentTab = 'postsTab';
let allPersonalData = [];
let allPostsData = [];
let currentPostDetail = null;
let currentModalPostId = null;

let chartTopEmployeesInstance = null;
let chartDivisionInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    setupDragAndDrop();
});

// Switch active tabs
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.sapa-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.remove('hidden');

    const targetBtn = document.getElementById(`tabBtn-${tabId}`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }

    currentTab = tabId;

    if (tabId === 'postsTab') renderPostPerformance();
    if (tabId === 'divisionTab') renderDivisionAnalytics();
    if (tabId === 'personalTab') renderPersonalAnalytics();
}

// Fetch main dashboard data from server
async function loadDashboardData() {
    const dateVal = document.getElementById('dateFilterSelect').value;

    try {
        // Fetch Summary KPI
        const resSummary = await fetch(`/api/summary?date=${encodeURIComponent(dateVal)}`);
        const summary = await resSummary.json();
        updateSummaryKPI(summary);

        // Populate Date Filter dropdown options
        populateDateFilter(summary.available_dates, dateVal);

        // Fetch Posts list & Personal Data
        await renderPostPerformance();
        await loadPersonalAnalytics();

    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

function updateSummaryKPI(s) {
    document.getElementById('statTotalPosts').textContent = s.total_posts || 0;
    document.getElementById('statTotalPegawai').textContent = s.total_employees || 0;
    document.getElementById('statTotalLikes').textContent = (s.total_like || 0).toLocaleString();
    document.getElementById('statIgLikes').textContent = `IG: ${(s.total_ig_like || 0).toLocaleString()}`;
    document.getElementById('statFbLikes').textContent = `FB: ${(s.total_fb_like || 0).toLocaleString()}`;

    document.getElementById('statTotalKomen').textContent = (s.total_komen || 0).toLocaleString();
    document.getElementById('statIgKomen').textContent = `IG: ${(s.total_ig_komen || 0).toLocaleString()}`;
    document.getElementById('statFbKomen').textContent = `FB: ${(s.total_fb_komen || 0).toLocaleString()}`;

    // Calculate Average Compliance
    const maxPossible = (s.total_posts || 1) * (s.total_employees || 75) * 2;
    const avgPct = maxPossible > 0 ? Math.round(((s.total_like || 0) / maxPossible) * 100) : 0;
    document.getElementById('statAvgCompliance').textContent = `${avgPct}%`;

    document.getElementById('statGrandTotal').textContent = (s.grand_total || 0).toLocaleString();
    if (document.getElementById('badgePostsCount')) {
        document.getElementById('badgePostsCount').textContent = s.total_posts || 0;
    }
}

function populateDateFilter(availableDates, selectedDate) {
    const select = document.getElementById('dateFilterSelect');
    const currVal = select.value;
    select.innerHTML = '<option value="" class="bg-slate-900 text-white">📅 Semua Tanggal Audit</option>';
    
    if (availableDates && availableDates.length) {
        availableDates.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = `📅 Batch Audit ${d}`;
            opt.className = "bg-slate-900 text-white";
            if (d === currVal || d === selectedDate) opt.selected = true;
            select.appendChild(opt);
        });
    }
}

// ==========================================
// 1. REKAPAN AUDIT PER POSTINGAN
// ==========================================
async function renderPostPerformance() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/posts?date=${encodeURIComponent(dateVal)}`);
    allPostsData = await res.json();

    document.getElementById('postFilteredCount').textContent = allPostsData.length;
    filterPostCards();
}

function filterPostCards() {
    const searchVal = (document.getElementById('postSearchInput').value || '').toLowerCase().trim();
    const container = document.getElementById('postsContainer');

    const filtered = allPostsData.filter(p => {
        return !searchVal || 
               (p.title && p.title.toLowerCase().includes(searchVal)) ||
               (p.ig_title && p.ig_title.toLowerCase().includes(searchVal)) ||
               (p.fb_title && p.fb_title.toLowerCase().includes(searchVal)) ||
               (p.date && p.date.includes(searchVal));
    });

    document.getElementById('postFilteredCount').textContent = filtered.length;

    if (!filtered || filtered.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-16 card-surface p-8">
                <i class="fa-regular fa-folder-open text-4xl text-slate-400 mb-3 block"></i>
                <h4 class="text-base font-bold text-[var(--text-dark)]">Tidak ada postingan audit yang cocok</h4>
                <p class="text-xs text-[var(--text-muted)] mt-1">Coba ubah kata kunci pencarian atau filter tanggal audit.</p>
            </div>
        `;
        return;
    }

    let html = '';
    filtered.forEach((p, idx) => {
        const comp = p.compliance || 0;
        const progressColor = comp >= 80 ? 'bg-emerald-500' : (comp >= 50 ? 'bg-amber-500' : 'bg-rose-500');

        html += `
            <div class="card-surface p-5 transition-all flex flex-col justify-between space-y-4 hover:shadow-xl group">
                <div>
                    <!-- Top Meta Badges -->
                    <div class="flex items-center justify-between gap-2 text-[11px] mb-2.5">
                        <span class="font-bold px-2 py-0.5 rounded-lg bg-[var(--pastel-gold-bg)] text-[var(--pastel-gold-text)] border border-[var(--pastel-gold-border)]">
                            📅 ${escapeHtml(p.date || '2026-08-18')}
                        </span>
                        <span class="text-[var(--text-muted)] font-mono text-[10px]">
                            🕒 ${escapeHtml(p.export_time || '-')}
                        </span>
                    </div>

                    <!-- Post Title -->
                    <h4 class="font-bold text-[var(--text-dark)] text-sm leading-snug line-clamp-2 group-hover:text-indigo-600 dark:group-hover:text-[var(--gold-accent)] transition-colors cursor-pointer" onclick="openPostDetailModal(${p.id})">
                        ${escapeHtml(p.title || 'Postingan Media Sosial')}
                    </h4>
                </div>

                <!-- Interaction Stats Mini Grid -->
                <div class="grid grid-cols-2 gap-2 text-xs bg-[var(--input-bg)] p-3 rounded-xl border border-[var(--border-color)]">
                    <div class="space-y-0.5">
                        <span class="text-[10px] font-bold text-pink-600 flex items-center gap-1">
                            <img src="/design/logo instagram.png" class="h-3 w-3 inline"> Instagram
                        </span>
                        <div class="text-[var(--text-dark)] font-medium text-[11px]">
                            <b class="text-emerald-600">${p.ig_like}</b> Suka • <b class="text-amber-600">${p.ig_komen}</b> Komen
                        </div>
                    </div>
                    <div class="space-y-0.5 border-l border-[var(--border-color)] pl-2">
                        <span class="text-[10px] font-bold text-blue-600 flex items-center gap-1">
                            <img src="/design/logo facebook.png" class="h-3 w-3 inline"> Facebook
                        </span>
                        <div class="text-[var(--text-dark)] font-medium text-[11px]">
                            <b class="text-emerald-600">${p.fb_like}</b> Suka • <b class="text-amber-600">${p.fb_komen}</b> Komen
                        </div>
                    </div>
                </div>

                <!-- Compliance Progress Bar -->
                <div class="space-y-1">
                    <div class="flex items-center justify-between text-[11px]">
                        <span class="text-[var(--text-muted)] font-semibold">Tingkat Partisipasi</span>
                        <span class="font-bold text-[var(--text-dark)]">${comp}%</span>
                    </div>
                    <div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                        <div class="${progressColor} h-2 rounded-full transition-all duration-500" style="width: ${Math.min(comp, 100)}%"></div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-2 border-t border-[var(--border-color)] flex items-center gap-2">
                    <button onclick="openPostDetailModal(${p.id})" class="flex-1 bg-[var(--navy-primary)] hover:bg-[var(--navy-light)] text-white font-bold text-xs py-2 px-3 rounded-xl transition-all shadow-md flex items-center justify-center space-x-1.5">
                        <i class="fa-solid fa-table-cells"></i>
                        <span>Lihat Rekap 75 ASN</span>
                    </button>
                    ${p.ig_url && p.ig_url !== '-' ? `<a href="${p.ig_url}" target="_blank" class="w-8 h-8 rounded-xl bg-pink-100 dark:bg-pink-950/40 hover:bg-pink-200 text-pink-600 flex items-center justify-center transition-all border border-pink-300 dark:border-pink-800" title="Buka Instagram Post"><i class="fa-brands fa-instagram"></i></a>` : ''}
                    ${p.fb_url && p.fb_url !== '-' ? `<a href="${p.fb_url}" target="_blank" class="w-8 h-8 rounded-xl bg-blue-100 dark:bg-blue-950/40 hover:bg-blue-200 text-blue-600 flex items-center justify-center transition-all border border-blue-300 dark:border-blue-800" title="Buka Facebook Post"><i class="fa-brands fa-facebook"></i></a>` : ''}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// ==============================================================
// 2. MODAL REKAPITULASI DETAIL 75 PEGAWAI PER POSTINGAN
// ==============================================================
async function openPostDetailModal(postId) {
    currentModalPostId = postId;
    const res = await fetch(`/api/post/detail?id=${postId}`);
    currentPostDetail = await res.json();

    if (!currentPostDetail) {
        alert('Data detail postingan tidak ditemukan.');
        return;
    }

    const d = currentPostDetail;

    // Header info
    document.getElementById('modalPostTitle').textContent = d.post_title || 'Rekapitulasi Audit Post';
    document.getElementById('modalPostDateBadge').textContent = `📅 Tanggal: ${d.audit_date}`;
    document.getElementById('modalPostExportTime').textContent = `🕒 Ekspor: ${d.export_time}`;

    // Metadata IG / FB links
    const igTitleElem = document.getElementById('modalPostIgTitleText');
    const igUrlElem = document.getElementById('modalPostIgUrl');
    if (d.ig_title && d.ig_title !== '-') {
        igTitleElem.textContent = d.ig_title;
        igUrlElem.href = d.ig_url || '#';
        igUrlElem.style.display = (d.ig_url && d.ig_url !== '-') ? 'inline' : 'none';
        document.getElementById('modalPostIgLinkRow').style.display = 'flex';
    } else {
        document.getElementById('modalPostIgLinkRow').style.display = 'none';
    }

    const fbTitleElem = document.getElementById('modalPostFbTitleText');
    const fbUrlElem = document.getElementById('modalPostFbUrl');
    if (d.fb_title && d.fb_title !== '-') {
        fbTitleElem.textContent = d.fb_title;
        fbUrlElem.href = d.fb_url || '#';
        fbUrlElem.style.display = (d.fb_url && d.fb_url !== '-') ? 'inline' : 'none';
        document.getElementById('modalPostFbLinkRow').style.display = 'flex';
    } else {
        document.getElementById('modalPostFbLinkRow').style.display = 'none';
    }

    // Mini Stats
    document.getElementById('modalStatLike').textContent = `${d.stats.total_like} (${d.stats.ig_like} IG / ${d.stats.fb_like} FB)`;
    document.getElementById('modalStatKomen').textContent = `${d.stats.total_komen} (${d.stats.ig_komen} IG / ${d.stats.fb_komen} FB)`;
    document.getElementById('modalStatPct').textContent = `${d.stats.ig_like_pct}%`;

    // Populate Division select filter
    populateModalDivisionFilter(Object.keys(d.grouped_by_divisi));

    // Render Matrix Table
    filterModalEmployeeTable();

    // Show modal
    const modal = document.getElementById('postDetailModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closePostDetailModal() {
    const modal = document.getElementById('postDetailModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    currentModalPostId = null;
    currentPostDetail = null;
}

function populateModalDivisionFilter(divisions) {
    const select = document.getElementById('modalDivisionFilter');
    select.innerHTML = '<option value="">🏢 Semua Divisi</option>';
    divisions.forEach(div => {
        const opt = document.createElement('option');
        opt.value = div;
        opt.textContent = div;
        select.appendChild(opt);
    });
}

function filterModalEmployeeTable() {
    if (!currentPostDetail) return;

    const searchVal = (document.getElementById('modalPostSearch').value || '').toLowerCase().trim();
    const divVal = document.getElementById('modalDivisionFilter').value;
    const tbody = document.getElementById('modalPostTableBody');

    let totalShown = 0;
    let html = '';

    const grouped = currentPostDetail.grouped_by_divisi;

    for (const [divName, items] of Object.entries(grouped)) {
        if (divVal && divVal !== divName) continue;

        const matchingItems = items.filter(emp => {
            return !searchVal ||
                   (emp.nama && emp.nama.toLowerCase().includes(searchVal)) ||
                   (emp.jabatan && emp.jabatan.toLowerCase().includes(searchVal));
        });

        if (matchingItems.length === 0) continue;

        totalShown += matchingItems.length;

        // Division Header Styling
        let divHeaderBg = 'bg-[var(--pastel-blue-bg)] text-[var(--pastel-blue-text)] border-[var(--pastel-blue-border)]';
        let divIcon = '🏢';
        if (divName.includes('KEPALA KANTOR WILAYAH')) {
            divHeaderBg = 'bg-[var(--pastel-gold-bg)] text-[var(--pastel-gold-text)] border-[var(--pastel-gold-border)]';
            divIcon = '👑';
        } else if (divName.includes('PELAYANAN HUKUM')) {
            divHeaderBg = 'bg-[var(--pastel-mint-bg)] text-[var(--pastel-mint-text)] border-[var(--pastel-mint-border)]';
            divIcon = '⚖️';
        } else if (divName.includes('PERATURAN PERUNDANG')) {
            divHeaderBg = 'bg-[var(--pastel-rose-bg)] text-[var(--pastel-rose-text)] border-[var(--pastel-rose-border)]';
            divIcon = '📜';
        } else if (divName.includes('TATA USAHA')) {
            divHeaderBg = 'bg-[var(--pastel-blue-bg)] text-[var(--pastel-blue-text)] border-[var(--pastel-blue-border)]';
            divIcon = '💼';
        }

        html += `
            <tr class="${divHeaderBg} border-y font-bold text-xs">
                <td colspan="7" class="py-2.5 px-4 tracking-wide">
                    ${divIcon} DIVISI: ${escapeHtml(divName)} (${matchingItems.length} Pegawai)
                </td>
            </tr>
        `;

        matchingItems.forEach(emp => {
            html += `
                <tr class="hover:bg-[var(--table-hover)] transition-colors">
                    <td class="py-2.5 px-3 text-center text-[var(--text-muted)] font-mono font-bold text-[11px]">${emp.no || '-'}</td>
                    <td class="py-2.5 px-3 font-extrabold text-[var(--text-dark)] text-xs">${escapeHtml(emp.nama)}</td>
                    <td class="py-2.5 px-3 text-[var(--text-muted)] font-medium text-[11px] max-w-xs truncate">${escapeHtml(emp.jabatan || '-')}</td>
                    <td class="py-2 px-3 text-center border-l border-[var(--border-color)]">${badgeStatus(emp.ig_like)}</td>
                    <td class="py-2 px-3 text-center border-r border-[var(--border-color)]">${badgeStatus(emp.ig_komen)}</td>
                    <td class="py-2 px-3 text-center">${badgeStatus(emp.fb_like)}</td>
                    <td class="py-2 px-3 text-center border-r border-[var(--border-color)]">${badgeStatus(emp.fb_komen)}</td>
                </tr>
            `;
        });
    }

    document.getElementById('modalFilteredCount').textContent = `${totalShown} Pegawai`;

    if (totalShown === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-[var(--text-muted)]">Tidak ada pegawai yang cocok dengan filter pencarian.</td></tr>`;
    } else {
        tbody.innerHTML = html;
    }
}

function exportSinglePostExcel() {
    if (!currentModalPostId) return;
    window.location.href = `/api/post/export-excel?id=${currentModalPostId}`;
}

// ==========================================
// 3. SINKRONISASI DARI FOLDER DOWNLOADS
// ==========================================
async function syncDownloadsFolder() {
    const syncBtn = document.getElementById('syncBtn');
    const syncStatus = document.getElementById('syncStatus');
    
    if (syncBtn) {
        syncBtn.disabled = true;
        syncBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Menyinkronkan...`;
    }

    if (syncStatus) {
        syncStatus.classList.remove('hidden');
        syncStatus.innerHTML = `<span class="text-indigo-500"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Memindai berkas PDF audit di folder Downloads...</span>`;
    }

    try {
        const res = await fetch('/api/sync-downloads', { method: 'POST' });
        const result = await res.json();

        if (res.ok && result.success) {
            if (syncStatus) {
                syncStatus.innerHTML = `<span class="text-emerald-600 font-bold"><i class="fa-solid fa-circle-check mr-1"></i> ${result.message}</span>`;
            }
            // Reload all dashboard views
            await loadDashboardData();
            alert(`✅ ${result.message}`);
        } else {
            if (syncStatus) {
                syncStatus.innerHTML = `<span class="text-rose-600 font-bold"><i class="fa-solid fa-circle-xmark mr-1"></i> Gagal: ${result.error || 'Terjadi kesalahan'}</span>`;
            }
        }
    } catch (err) {
        if (syncStatus) {
            syncStatus.innerHTML = `<span class="text-rose-600 font-bold"><i class="fa-solid fa-circle-xmark mr-1"></i> Error: ${err.message}</span>`;
        }
    } finally {
        if (syncBtn) {
            syncBtn.disabled = false;
            syncBtn.innerHTML = `<i class="fa-solid fa-cloud-arrow-down mr-1"></i> <span class="hidden md:inline">Sinkronkan Downloads</span>`;
        }
    }
}

// ==========================================
// 4. ANALISIS PERSONAL & LEADERBOARD
// ==========================================
async function loadPersonalAnalytics() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/personal?date=${encodeURIComponent(dateVal)}`);
    allPersonalData = await res.json();

    populateDivisionFilter(allPersonalData);
    filterPersonalTable();
    renderTopEmployeesChart(allPersonalData);
}

function renderPersonalAnalytics() {
    filterPersonalTable();
    renderTopEmployeesChart(allPersonalData);
}

function populateDivisionFilter(data) {
    const select = document.getElementById('divisionFilterSelect');
    if (!select) return;
    const currVal = select.value;
    
    const divisions = [...new Set(data.map(d => d.divisi).filter(Boolean))];
    select.innerHTML = '<option value="">🏢 Semua Divisi</option>';

    divisions.sort().forEach(div => {
        const opt = document.createElement('option');
        opt.value = div;
        opt.textContent = div;
        opt.className = "bg-slate-900 text-white";
        if (div === currVal) opt.selected = true;
        select.appendChild(opt);
    });
}

function filterPersonalTable() {
    const searchInput = document.getElementById('personalSearchInput');
    const searchVal = searchInput ? (searchInput.value || '').toLowerCase().trim() : '';
    const divSelect = document.getElementById('divisionFilterSelect');
    const divVal = divSelect ? divSelect.value : '';

    const filtered = allPersonalData.filter(emp => {
        const matchSearch = !searchVal || 
                            (emp.nama && emp.nama.toLowerCase().includes(searchVal)) || 
                            (emp.jabatan && emp.jabatan.toLowerCase().includes(searchVal));
        const matchDiv = !divVal || emp.divisi === divVal;
        return matchSearch && matchDiv;
    });

    const badge = document.getElementById('personalCountBadge');
    if (badge) badge.textContent = filtered.length;
    renderPersonalTable(filtered);
}

function renderPersonalTable(data) {
    const tbody = document.getElementById('personalTableBody');
    if (!tbody) return;

    if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-[var(--text-muted)]">Tidak ada pegawai yang sesuai dengan filter.</td></tr>`;
        return;
    }

    let html = '';
    data.forEach((emp, index) => {
        const comp = emp.like_compliance || 0;
        const compColor = comp >= 80 ? 'text-emerald-600 font-extrabold' : (comp >= 50 ? 'text-amber-600 font-extrabold' : 'text-rose-600 font-extrabold');

        html += `
            <tr onclick="openEmployeeModal('${escapeJsString(emp.nama)}')" class="hover:bg-[var(--table-hover)] cursor-pointer transition-colors group">
                <td class="py-3 px-4 text-xs font-bold text-[var(--text-muted)]">${index + 1}</td>
                <td class="py-3 px-4">
                    <div class="font-extrabold text-[var(--text-dark)] group-hover:text-indigo-600 dark:group-hover:text-[var(--gold-accent)] transition-colors text-xs">${escapeHtml(emp.nama)}</div>
                    <div class="text-[11px] text-[var(--text-muted)] font-medium truncate max-w-xs">${escapeHtml(emp.jabatan || '')}</div>
                </td>
                <td class="py-3 px-4 text-center text-xs">
                    <span class="font-bold text-rose-600">${emp.ig_like}</span> Like • 
                    <span class="font-bold text-amber-600">${emp.ig_komen}</span> Komen
                </td>
                <td class="py-3 px-4 text-center text-xs">
                    <span class="font-bold text-rose-600">${emp.fb_like}</span> Like • 
                    <span class="font-bold text-amber-600">${emp.fb_komen}</span> Komen
                </td>
                <td class="py-3 px-4 text-center text-xs font-extrabold text-[var(--text-dark)]">
                    ${emp.total_like}
                </td>
                <td class="py-3 px-4 text-center text-xs ${compColor}">
                    ${comp}%
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function renderTopEmployeesChart(data) {
    const ctx = document.getElementById('chartTopEmployees');
    if (!ctx) return;

    const top10 = data.slice(0, 10);
    const labels = top10.map(d => d.nama.length > 16 ? d.nama.substring(0, 14) + '...' : d.nama);
    const likes = top10.map(d => d.total_like);
    const komens = top10.map(d => d.total_komen);

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#F8FAFC' : '#1E293B';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';

    if (chartTopEmployeesInstance) chartTopEmployeesInstance.destroy();

    chartTopEmployeesInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Likes', data: likes, backgroundColor: '#1B2C5D', borderRadius: 6 },
                { label: 'Komen', data: komens, backgroundColor: '#FFCB05', borderRadius: 6 }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: 'bold', size: 11 } } }
            },
            scales: {
                x: { ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 10 } }, grid: { color: gridColor } },
                y: { ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: 'bold', size: 11 } }, grid: { display: false } }
            }
        }
    });
}

// ==========================================
// 5. ANALISIS PER DIVISI
// ==========================================
async function renderDivisionAnalytics() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/divisions?date=${encodeURIComponent(dateVal)}`);
    const divisions = await res.json();

    const tbody = document.getElementById('divisionTableBody');
    if (!divisions || divisions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-[var(--text-muted)]">Belum ada data divisi.</td></tr>`;
        return;
    }

    let html = '';
    divisions.forEach(d => {
        html += `
            <tr class="hover:bg-[var(--table-hover)] transition-colors text-xs">
                <td class="py-3 px-4 font-bold text-[var(--text-dark)]">${escapeHtml(d.divisi)}</td>
                <td class="py-3 px-4 text-center text-[var(--text-dark)] font-bold">${d.total_pegawai}</td>
                <td class="py-3 px-4 text-center text-rose-600 font-extrabold">${d.total_like}</td>
                <td class="py-3 px-4 text-center text-amber-600 font-extrabold">${d.total_komen}</td>
                <td class="py-3 px-4 text-center text-indigo-600 dark:text-[var(--gold-accent)] font-extrabold">${d.total_interaction}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;

    // Render Chart Division
    const ctx = document.getElementById('chartDivision');
    if (!ctx) return;

    const labels = divisions.map(d => d.divisi.replace('DIVISI: ', '').replace('BAGIAN ', ''));
    const likes = divisions.map(d => d.total_like);
    const komens = divisions.map(d => d.total_komen);

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#F8FAFC' : '#1E293B';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';

    if (chartDivisionInstance) chartDivisionInstance.destroy();

    chartDivisionInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Likes', data: likes, backgroundColor: '#1B2C5D', borderRadius: 8 },
                { label: 'Komen', data: komens, backgroundColor: '#FFCB05', borderRadius: 8 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: textColor, font: { family: 'Plus Jakarta Sans', weight: 'bold', size: 11 } } }
            },
            scales: {
                x: { ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 10 } }, grid: { display: false } },
                y: { ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 10 } }, grid: { color: gridColor } }
            }
        }
    });
}

// ==========================================
// 6. EMPLOYEE DETAIL MODAL
// ==========================================
async function openEmployeeModal(empName) {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/employee/detail?name=${encodeURIComponent(empName)}&date=${encodeURIComponent(dateVal)}`);
    const detail = await res.json();

    document.getElementById('modalEmpName').textContent = detail.nama;
    document.getElementById('modalEmpMeta').textContent = `${detail.jabatan || 'N/A'} | ${detail.divisi || 'N/A'}`;

    const tbody = document.getElementById('modalEmpPostList');
    let html = '';
    detail.posts.forEach(p => {
        html += `
            <tr class="hover:bg-[var(--table-hover)] transition-colors">
                <td class="py-2.5 px-3 max-w-sm">
                    <div class="font-bold text-[var(--text-dark)] truncate">${escapeHtml(p.title)}</div>
                    <div class="text-[10px] text-[var(--text-muted)] font-semibold">📅 ${p.date} • 🕒 ${p.export_time || '-'}</div>
                </td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.ig_like)}</td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.ig_komen)}</td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.fb_like)}</td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.fb_komen)}</td>
                <td class="py-2.5 px-3 text-center">
                    <button onclick="closeEmployeeModal(); openPostDetailModal(${p.post_id})" class="text-indigo-600 dark:text-[var(--gold-accent)] hover:underline text-xs font-bold">
                        Buka Post
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html || `<tr><td colspan="6" class="text-center py-6 text-[var(--text-muted)]">Tidak ada data rincian post.</td></tr>`;

    const modal = document.getElementById('employeeModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeEmployeeModal() {
    const modal = document.getElementById('employeeModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function badgeStatus(status) {
    if (status === 'SUDAH') return `<span class="badge-sudah text-[10px] font-bold">SUDAH</span>`;
    if (status === 'BELUM') return `<span class="badge-belum text-[10px] font-bold">BELUM</span>`;
    return `<span class="badge-none text-[11px] font-medium">-</span>`;
}

// ==========================================
// 7. EXPORT HELPERS
// ==========================================
function exportToPdf() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    window.location.href = `/api/export-pdf?date=${encodeURIComponent(dateVal)}`;
}

function exportToExcel() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    window.location.href = `/api/export-excel?date=${encodeURIComponent(dateVal)}`;
}

// ==========================================
// 8. UPLOAD & DRAG DROP
// ==========================================
function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('border-brand-500', 'bg-slate-900'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('border-brand-500', 'bg-slate-900'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        uploadFiles(files);
    });
}

async function uploadFiles(files) {
    if (!files || files.length === 0) return;

    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.classList.remove('hidden');
    statusDiv.innerHTML = `<span class="text-brand-400"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Meng-upload dan mengolah ${files.length} file PDF...</span>`;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const result = await res.json();

        if (res.ok && result.success) {
            statusDiv.innerHTML = `<span class="text-emerald-400 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i> Berhasil mengunggah ${result.saved_count} file PDF!</span>`;
            await loadDashboardData();
        } else {
            statusDiv.innerHTML = `<span class="text-rose-400"><i class="fa-solid fa-circle-xmark mr-1"></i> Gagal: ${result.error || 'Terjadi kesalahan'}</span>`;
        }
    } catch (err) {
        statusDiv.innerHTML = `<span class="text-rose-400"><i class="fa-solid fa-circle-xmark mr-1"></i> Error: ${err.message}</span>`;
    }
}

async function clearAllData() {
    if (!confirm('Apakah Anda yakin ingin menghapus seluruh data audit dari database?')) return;
    try {
        const res = await fetch('/api/clear', { method: 'POST' });
        const result = await res.json();
        if (result.success) {
            alert('Semua data berhasil dibersihkan.');
            loadDashboardData();
        }
    } catch (err) {
        alert('Gagal membersihkan data: ' + err.message);
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeJsString(str) {
    if (!str) return '';
    return String(str).replace(/'/g, "\\'");
}
