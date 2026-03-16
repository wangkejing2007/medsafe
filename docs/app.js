document.addEventListener('DOMContentLoaded', () => {
    const drugInput = document.getElementById('drug-input');
    const addBtn = document.getElementById('add-drug');
    const drugListContainer = document.getElementById('drug-list');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsSection = document.getElementById('results-section');
    const restartBtn = document.getElementById('restart-btn');
    const detailContainer = document.getElementById('detail-results');
    const statusCard = document.getElementById('status-card');
    
    let drugs = [];
    let currentView = 'elderly'; // default
    let lastResult = null;

    // --- View Switching ---
    const viewBtns = {
        'elderly': document.getElementById('btn-elderly'),
        'family': document.getElementById('btn-family'),
        'doctor': document.getElementById('btn-doctor')
    };

    Object.keys(viewBtns).forEach(mode => {
        viewBtns[mode].addEventListener('click', () => {
            Object.values(viewBtns).forEach(b => b.classList.remove('active'));
            viewBtns[mode].classList.add('active');
            currentView = mode;
            if (lastResult) renderResults(lastResult);
        });
    });

    // --- Drug Selection ---
    addBtn.addEventListener('click', () => {
        const value = drugInput.value.trim();
        if (value && !drugs.includes(value)) {
            drugs.push(value);
            renderTags();
            drugInput.value = '';
            analyzeBtn.disabled = drugs.length < 2;
        }
    });

    drugInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addBtn.click();
    });

    function renderTags() {
        drugListContainer.innerHTML = '';
        drugs.forEach((drug, index) => {
            const tag = document.createElement('div');
            tag.className = 'drug-tag';
            tag.innerHTML = `
                ${drug}
                <span class="remove-btn" onclick="removeDrug(${index})">×</span>
            `;
            drugListContainer.appendChild(tag);
        });
    }

    window.removeDrug = (index) => {
        drugs.splice(index, 1);
        renderTags();
        analyzeBtn.disabled = drugs.length < 2;
    };

    // --- Analysis ---
    analyzeBtn.addEventListener('click', async () => {
        analyzeBtn.disabled = true;
        analyzeBtn.innerText = '正在分析中...';
        
        // Detect if running on GitHub Pages or locally
        const isGitHub = window.location.hostname.includes('github.io');
        
        try {
            let data;
            if (isGitHub) {
                // Simulated API call for Demo
                await new Promise(resolve => setTimeout(resolve, 2000));
                data = getSimulatedResult(drugs);
            } else {
                // Real API call for Local
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ drugs })
                });
                data = await response.json();
            }
            lastResult = data;
            renderResults(data);
        } catch (error) {
            console.error('Analysis failed', error);
            alert('分析失敗，請檢查 API 連線');
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i data-lucide="search"></i>開始 AI 智慧分析';
            if (window.lucide) window.lucide.createIcons();
        }
    });

    // Helper for Demo Simulation
    function getSimulatedResult(drugList) {
        // Simple logic for demo: If Aspirin + Warfarin, show high risk. Else show safe.
        const normalized = drugList.map(d => d.toLowerCase());
        const isAspirin = normalized.some(d => d.includes('aspirin') || d.includes('阿斯匹靈'));
        const isWarfarin = normalized.some(d => d.includes('warfarin') || d.includes('華法林'));

        if (isAspirin && isWarfarin) {
            return {
                overall_level: 'red',
                disclaimer: '免責聲明：此為展示模式，模擬分析結果僅供參考。',
                pair_results: [{
                    drug_a_zh: '阿斯匹靈', drug_a_input: 'Aspirin',
                    drug_b_zh: '華法林', drug_b_input: 'Warfarin',
                    level: 'red',
                    reasons: [{
                        description: '嚴重出血風險顯著增加，包括腸胃道出血和顱內出血。',
                        mechanism: '兩者皆具抗凝血/抗血小板作用，併用會產生加成效應，極大增加出血機率。'
                    }]
                }]
            };
        }
        
        return {
            overall_level: 'green',
            disclaimer: '免責聲明：此為展示模式，模擬分析結果僅供參考。',
            pair_results: []
        };
    }

    // --- Restart Analysis ---
    restartBtn.addEventListener('click', () => {
        // Reset state
        drugs = [];
        lastResult = null;
        
        // Reset UI
        renderTags();
        analyzeBtn.disabled = true;
        
        // Hide results section
        resultsSection.classList.add('results-hidden');
        
        // Explicitly clear contents to prevent any ghost results
        const detailsContainer = document.getElementById('detail-results');
        if (detailsContainer) detailsContainer.innerHTML = '';
        
        const summaryIcon = document.getElementById('summary-icon-container');
        if (summaryIcon) summaryIcon.innerHTML = '';
        
        const statusText = document.getElementById('status-text');
        if (statusText) statusText.innerText = '';
        
        const statusSubtext = document.getElementById('status-subtext');
        if (statusSubtext) statusSubtext.innerText = '';
        
        drugInput.value = '';
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Focus input
        drugInput.focus();
    });

    function renderResults(data) {
        // Prevent showing results if the analysis was restarted during fetch
        if (!lastResult || drugs.length === 0) return;

        resultsSection.classList.remove('results-hidden');
        
        const statusCard = document.getElementById('overall-status');
        const statusText = document.getElementById('status-text');
        const statusSubtext = document.getElementById('status-subtext');
        const detailsContainer = document.getElementById('detail-results');
        
        // Update Card Class for Color Coding
        statusCard.className = `glass-card status-card status-${data.overall_level}`;
        
        // Update Summary Icon with Pure SVG (Guarantees true transparency and flat vector look)
        const iconContainer = document.getElementById('summary-icon-container');
        if (iconContainer) {
            const riskLevel = data.overall_level;
            const svgMap = {
                'red': `
                    <svg class="status-svg-flat pulse-red" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="11" fill="#ef4444"/>
                        <path d="M12 7V13" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                        <circle cx="12" cy="17" r="1.25" fill="white"/>
                    </svg>`,
                'yellow': `
                    <svg class="status-svg-flat" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="11" fill="#f59e0b"/>
                        <path d="M12 7V13" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                        <circle cx="12" cy="17" r="1.25" fill="white"/>
                    </svg>`,
                'green': `
                    <svg class="status-svg-flat" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="11" fill="#10b981"/>
                        <path d="M12 12L10.5 10.5M12 12L15.5 8.5M12 12L9 15L7.5 13.5" stroke="white" stroke-width="0" opacity="0"/>
                        <path d="M7 12.5L10 15.5L17 8.5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>`
            };
            iconContainer.innerHTML = svgMap[riskLevel] || svgMap['green'];
        }
        
        // Update Text
        if (statusText) statusText.innerText = ''; 
        if (statusSubtext) {
            statusSubtext.innerText = data.overall_level === 'green' 
                ? '您的用藥目前看起來非常安全。' 
                : '偵測到潛在交互作用，建議諮詢醫師或藥師。';
        }
        
        document.getElementById('disclaimer-text').innerText = data.disclaimer;

        detailsContainer.innerHTML = '';
        detailsContainer.className = `detail-container view-${currentView}`; // Keep this line

        if (!data.pair_results || data.pair_results.length === 0) {
            detailsContainer.innerHTML = '<div class="glassmorphism brand-shadow" style="padding: 2rem; text-align: center; color: var(--text-muted);"><p>未偵測到顯著的交互作用。</p></div>';
            if (window.lucide) { // Ensure lucide is available
                window.lucide.createIcons();
            }
            return;
        }

        data.pair_results.forEach(res => {
            const div = document.createElement('div');
            div.className = 'detail-item';
            if (res.level === 'red') div.classList.add('risk-high');
            
            const reasonsHtml = res.reasons.map(r => `
                <div class="reason-block">
                    <p><i data-lucide="help-circle" style="width:14px;height:14px;vertical-align:middle;margin-right:4px;color:var(--accent-color)"></i><strong>原因：</strong>${r.description}</p>
                    <p class="mechanism"><i data-lucide="microscope" style="width:14px;height:14px;vertical-align:middle;margin-right:4px"></i><strong>藥理機制：</strong>${r.mechanism}</p>
                </div>
            `).join('');

            const severityClassMap = { 'red': 'high', 'yellow': 'medium', 'green': 'low' };
            const severityClass = severityClassMap[res.level] || 'low';
            
            const imgNameMap = { 'red': '紅燈', 'yellow': '黃燈', 'green': '綠燈' };
            const imgName = imgNameMap[res.level] || '綠燈';

            const nameA = res.drug_a_zh === res.drug_a_input ? res.drug_a_zh : `${res.drug_a_zh} (${res.drug_a_input})`;
            const nameB = res.drug_b_zh === res.drug_b_input ? res.drug_b_zh : `${res.drug_b_zh} (${res.drug_b_input})`;

            div.innerHTML = `
                <div class="detail-header">
                    <div class="pair-names">
                        <div class="pill-3d"></div>
                        ${nameA} + ${nameB}
                    </div>
                    <div class="traffic-image-box">
                        <img src="${imgName}.webp" class="detail-traffic-img" alt="${imgName}">
                    </div>
                </div>
                ${reasonsHtml}
            `;
            detailsContainer.appendChild(div);
        });

        // 3. Refresh Lucide Icons for dynamic content
        if (window.lucide) {
            window.lucide.createIcons();
        }

        // 捲動到結果區
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
});
