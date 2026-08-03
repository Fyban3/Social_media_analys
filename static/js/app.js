// Global State Variables
let currentTab = 'personalTab';
let allPersonalData = [];
let chartTopEmployeesInstance = null;
let chartDivisionInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    setupDragAndDrop();
});

// Switch active tabs
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active', 'border-brand-500', 'text-brand-400', 'bg-slate-900/50');
        btn.classList.add('border-transparent', 'text-slate-400');
    });

    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.remove('hidden');

    const targetBtn = document.getElementById(`tabBtn-${tabId}`);
    if (targetBtn) {
        targetBtn.classList.add('active', 'border-brand-500', 'text-brand-400', 'bg-slate-900/50');
        targetBtn.classList.remove('border-transparent', 'text-slate-400');
    }

    currentTab = tabId;

    if (tabId === 'divisionTab') renderDivisionAnalytics();
    if (tabId === 'postsTab') renderPostPerformance();
}

// Fetch main dashboard data from server
async function loadDashboardData() {
    const dateVal = document.getElementById('dateFilterSelect').value;

    try {
        // Fetch Summary KPI
        const resSummary = await fetch(`/api/summary?date=${encodeURIComponent(dateVal)}`);
        const summary = await resSummary.json();
        updateSummaryKPI(summary);

        // Populate Date Filter dropdown options if not yet populated
        populateDateFilter(summary.available_dates, dateVal);

        // Fetch Personal Analytics Data
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

    document.getElementById('statTotalShares').textContent = (s.total_share || 0).toLocaleString();
    document.getElementById('statGrandTotal').textContent = (s.grand_total || 0).toLocaleString();
}

function populateDateFilter(availableDates, selectedDate) {
    const select = document.getElementById('dateFilterSelect');
    const currVal = select.value;
    select.innerHTML = '<option value="">📅 Semua Tanggal Audit</option>';
    
    if (availableDates && availableDates.length) {
        availableDates.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = `📅 Batch Audit ${d}`;
            if (d === currVal || d === selectedDate) opt.selected = true;
            select.appendChild(opt);
        });
    }
}

// Load Personal Analytics
async function loadPersonalAnalytics() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/personal?date=${encodeURIComponent(dateVal)}`);
    allPersonalData = await res.json();

    populateDivisionFilter(allPersonalData);
    filterPersonalTable();
    renderTopEmployeesChart(allPersonalData);
}

function populateDivisionFilter(data) {
    const select = document.getElementById('divisionFilterSelect');
    const currVal = select.value;
    
    const divisions = [...new Set(data.map(d => d.divisi).filter(Boolean))];
    select.innerHTML = '<option value="">🏢 Semua Divisi</option>';

    divisions.sort().forEach(div => {
        const opt = document.createElement('option');
        opt.value = div;
        opt.textContent = div;
        if (div === currVal) opt.selected = true;
        select.appendChild(opt);
    });
}

function filterPersonalTable() {
    const searchVal = document.getElementById('personalSearchInput').value.toLowerCase().strip ? document.getElementById('personalSearchInput').value.toLowerCase().strip() : document.getElementById('personalSearchInput').value.toLowerCase();
    const divVal = document.getElementById('divisionFilterSelect').value;

    const filtered = allPersonalData.filter(emp => {
        const matchSearch = !searchVal || emp.nama.toLowerCase().includes(searchVal) || (emp.jabatan && emp.jabatan.toLowerCase().includes(searchVal));
        const matchDiv = !divVal || emp.divisi === divVal;
        return matchSearch && matchDiv;
    });

    document.getElementById('personalCountBadge').textContent = filtered.length;
    renderPersonalTable(filtered);
}

function renderPersonalTable(data) {
    const tbody = document.getElementById('personalTableBody');

    if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-8 text-slate-500">Tidak ada pegawai yang sesuai dengan filter.</td></tr>`;
        return;
    }

    let html = '';
    data.forEach((emp, index) => {
        html += `
            <tr onclick="openEmployeeModal('${escapeJsString(emp.nama)}')" class="hover:bg-slate-800/60 cursor-pointer transition-colors group">
                <td class="py-3 px-4 text-xs font-semibold text-slate-400 group-hover:text-white">${index + 1}</td>
                <td class="py-3 px-4">
                    <div class="font-bold text-slate-100 group-hover:text-brand-300 transition-colors">${escapeHtml(emp.nama)}</div>
                    <div class="text-[11px] text-slate-400 truncate max-w-xs">${escapeHtml(emp.jabatan || '')}</div>
                </td>
                <td class="py-3 px-4 text-center text-xs">
                    <span class="font-semibold text-rose-400">${emp.ig_like}</span> Like / 
                    <span class="font-semibold text-amber-300">${emp.ig_komen}</span> Komen
                </td>
                <td class="py-3 px-4 text-center text-xs">
                    <span class="font-semibold text-rose-400">${emp.fb_like}</span> Like / 
                    <span class="font-semibold text-amber-300">${emp.fb_komen}</span> Komen
                </td>
                <td class="py-3 px-4 text-center font-bold text-rose-400">${emp.total_like}</td>
                <td class="py-3 px-4 text-center font-bold text-amber-300">${emp.total_komen}</td>
                <td class="py-3 px-4 text-center font-extrabold text-yellow-400 text-sm">
                    <span class="bg-yellow-400/10 border border-yellow-400/30 px-2.5 py-1 rounded-lg">
                        ${emp.total_interaction}
                    </span>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// Chart: Top 10 Employees
function renderTopEmployeesChart(data) {
    const ctx = document.getElementById('chartTopEmployees').getContext('2d');
    const top10 = [...data].slice(0, 10);

    const labels = top10.map(d => d.nama.length > 18 ? d.nama.substring(0, 18) + '...' : d.nama);
    const likesData = top10.map(d => d.total_like);
    const komenData = top10.map(d => d.total_komen);

    if (chartTopEmployeesInstance) {
        chartTopEmployeesInstance.destroy();
    }

    chartTopEmployeesInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Total Likes',
                    data: likesData,
                    backgroundColor: '#f43f5e',
                    borderRadius: 6
                },
                {
                    label: 'Total Komen',
                    data: komenData,
                    backgroundColor: '#f59e0b',
                    borderRadius: 6
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    ticks: { color: '#64748b' },
                    grid: { color: 'rgba(51, 65, 85, 0.3)' }
                },
                y: {
                    stacked: true,
                    ticks: { color: '#cbd5e1', font: { size: 11 } },
                    grid: { display: false }
                }
            }
        }
    });
}

// Render Division Analytics
async function renderDivisionAnalytics() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/divisions?date=${encodeURIComponent(dateVal)}`);
    const divisions = await res.json();

    const tbody = document.getElementById('divisionTableBody');
    let html = '';
    divisions.forEach(d => {
        html += `
            <tr class="hover:bg-slate-800/60">
                <td class="py-3 px-4 font-semibold text-slate-100">${escapeHtml(d.divisi)}</td>
                <td class="py-3 px-4 text-center text-slate-400 font-medium">${d.total_pegawai}</td>
                <td class="py-3 px-4 text-center font-bold text-rose-400">${d.total_like}</td>
                <td class="py-3 px-4 text-center font-bold text-amber-300">${d.total_komen}</td>
                <td class="py-3 px-4 text-center font-extrabold text-yellow-400">${d.total_interaction}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html || `<tr><td colspan="5" class="text-center py-6 text-slate-500">Tidak ada data divisi.</td></tr>`;

    // Division Chart
    const ctx = document.getElementById('chartDivision').getContext('2d');
    const labels = divisions.map(d => d.divisi);
    const likes = divisions.map(d => d.total_like);
    const komens = divisions.map(d => d.total_komen);

    if (chartDivisionInstance) chartDivisionInstance.destroy();

    chartDivisionInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Likes', data: likes, backgroundColor: '#6366f1', borderRadius: 8 },
                { label: 'Komen', data: komens, backgroundColor: '#10b981', borderRadius: 8 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#94a3b8' } }
            },
            scales: {
                x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
                y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(51, 65, 85, 0.3)' } }
            }
        }
    });
}

// Render Post Performance
async function renderPostPerformance() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const res = await fetch(`/api/posts?date=${encodeURIComponent(dateVal)}`);
    const posts = await res.json();

    const container = document.getElementById('postsContainer');
    if (!posts || posts.length === 0) {
        container.innerHTML = `<div class="col-span-full text-center py-12 text-slate-500">Belum ada post ter-audit.</div>`;
        return;
    }

    let html = '';
    posts.forEach(p => {
        html += `
            <div class="bg-slate-950/80 border border-slate-800 hover:border-brand-500/50 rounded-2xl p-5 transition-all flex flex-col justify-between space-y-4">
                <div>
                    <div class="text-xs text-brand-400 font-semibold mb-1">📅 Audit: ${p.date}</div>
                    <h4 class="font-bold text-slate-100 text-sm line-clamp-2 hover:line-clamp-none">${escapeHtml(p.title)}</h4>
                </div>

                <div class="grid grid-cols-2 gap-2 text-xs bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div>
                        <span class="text-slate-400 block">Instagram</span>
                        <span class="font-bold text-rose-400">${p.ig_like} Like</span> • 
                        <span class="font-bold text-amber-300">${p.ig_komen} Komen</span>
                    </div>
                    <div>
                        <span class="text-slate-400 block">Facebook</span>
                        <span class="font-bold text-rose-400">${p.fb_like} Like</span> • 
                        <span class="font-bold text-amber-300">${p.fb_komen} Komen</span>
                    </div>
                </div>

                <div class="flex items-center space-x-2">
                    ${p.ig_url ? `<a href="${p.ig_url}" target="_blank" class="flex-1 text-center bg-gradient-to-r from-pink-600 to-rose-600 hover:opacity-90 text-white text-xs font-semibold py-2 px-3 rounded-xl transition-all"><i class="fa-brands fa-instagram mr-1"></i> IG Post</a>` : ''}
                    ${p.fb_url ? `<a href="${p.fb_url}" target="_blank" class="flex-1 text-center bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold py-2 px-3 rounded-xl transition-all"><i class="fa-brands fa-facebook mr-1"></i> FB Post</a>` : ''}
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Employee Detail Modal Drill-down
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
            <tr class="hover:bg-slate-800/40">
                <td class="py-2.5 px-3 max-w-sm">
                    <div class="font-semibold text-slate-100 truncate">${escapeHtml(p.title)}</div>
                    <div class="text-[10px] text-slate-500">${p.date}</div>
                </td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.ig_like)}</td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.ig_komen)}</td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.fb_like)}</td>
                <td class="py-2.5 px-3 text-center">${badgeStatus(p.fb_komen)}</td>
                <td class="py-2.5 px-3 text-center">
                    ${(p.ig_like === 'SUDAH' || p.fb_like === 'SUDAH') ? '<span class="text-emerald-400 font-bold"><i class="fa-solid fa-check"></i> Aktif</span>' : '<span class="text-slate-500">-</span>'}
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html || `<tr><td colspan="6" class="text-center py-6 text-slate-500">Tidak ada data rincian post.</td></tr>`;

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
    if (status === 'SUDAH') return `<span class="badge-sudah px-2 py-0.5 rounded text-[11px] font-bold">SUDAH</span>`;
    if (status === 'BELUM') return `<span class="badge-belum px-2 py-0.5 rounded text-[11px] font-bold">BELUM</span>`;
    return `<span class="badge-none px-2 py-0.5 rounded text-[11px] font-medium">-</span>`;
}

// Ingestion & File Upload Logic
async function importFromFolder() {
    const folderPath = document.getElementById('folderPathInput').value;
    const statusDiv = document.getElementById('importStatus');
    statusDiv.classList.remove('hidden');
    statusDiv.innerHTML = `<span class="text-indigo-400"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Memproses file PDF dari folder...</span>`;

    try {
        const res = await fetch('/api/import-folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder_path: folderPath })
        });
        const result = await res.json();

        if (res.ok && result.success) {
            statusDiv.innerHTML = `<span class="text-emerald-400 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i> Berhasil meng-import ${result.saved_count} file PDF audit!</span>`;
            loadDashboardData();
        } else {
            statusDiv.innerHTML = `<span class="text-rose-400"><i class="fa-solid fa-circle-xmark mr-1"></i> Gagal: ${result.error || 'Terjadi kesalahan'}</span>`;
        }
    } catch (err) {
        statusDiv.innerHTML = `<span class="text-rose-400"><i class="fa-solid fa-circle-xmark mr-1"></i> Error: ${err.message}</span>`;
    }
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
            statusDiv.innerHTML = `<span class="text-emerald-400 font-semibold"><i class="fa-solid fa-circle-check mr-1"></i> Berhasil meng-upload ${result.saved_count} file PDF audit!</span>`;
            loadDashboardData();
        } else {
            statusDiv.innerHTML = `<span class="text-rose-400"><i class="fa-solid fa-circle-xmark mr-1"></i> Gagal upload: ${result.error || 'Terjadi kesalahan'}</span>`;
        }
    } catch (err) {
        statusDiv.innerHTML = `<span class="text-rose-400"><i class="fa-solid fa-circle-xmark mr-1"></i> Error: ${err.message}</span>`;
    }
}

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

// Export to PDF
function exportToPdf() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const divVal = document.getElementById('divisionFilterSelect').value;
    const searchVal = document.getElementById('personalSearchInput').value;

    window.location.href = `/api/export-pdf?date=${encodeURIComponent(dateVal)}&divisi=${encodeURIComponent(divVal)}&search=${encodeURIComponent(searchVal)}`;
}

// Export to Excel
function exportToExcel() {
    const dateVal = document.getElementById('dateFilterSelect').value;
    const divVal = document.getElementById('divisionFilterSelect').value;
    const searchVal = document.getElementById('personalSearchInput').value;

    window.location.href = `/api/export-excel?date=${encodeURIComponent(dateVal)}&divisi=${encodeURIComponent(divVal)}&search=${encodeURIComponent(searchVal)}`;
}

// Clear all database records
async function clearAllData() {
    if (!confirm('Apakah Anda yakin ingin menghapus seluruh data audit yang tersimpan?')) return;

    try {
        const res = await fetch('/api/clear', { method: 'POST' });
        if (res.ok) {
            alert('Semua data audit berhasil direset.');
            loadDashboardData();
        }
    } catch (err) {
        alert('Gagal menghapus data: ' + err.message);
    }
}

// Helpers
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeJsString(str) {
    if (!str) return '';
    return str.replace(/'/g, "\\'");
}
