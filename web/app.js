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
    let drugDisplayNames = {}; // Map generic to ZH display
    let currentView = 'elderly'; // default
    let lastResult = null;

    // --- Deployment Config ---
    // Make PRODUCTION_API_URL accessible to both add and analyze routines
    const PRODUCTION_API_URL = 'https://medsafe-backend-vhvb.onrender.com';

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
    addBtn.addEventListener('click', async () => {
        const value = drugInput.value.trim();
        if (!value) return;
        
        if (drugs.includes(value)) {
            alert('此藥品已在清單中');
            return;
        }

        // Show loading state
        addBtn.disabled = true;
        addBtn.innerText = '驗證中...';

        try {
            const isGitHub = window.location.hostname.includes('github.io');
            const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
            
            // Use search endpoint for better validation data
            // If local, use relative path to talk to local backend. If production/GitHub, use Render URL.
            const apiUrl = isLocal ? `/api/drug/search?query=${encodeURIComponent(value)}` : 
                          (PRODUCTION_API_URL ? `${PRODUCTION_API_URL}/api/drug/search?query=${encodeURIComponent(value)}` : `/api/drug/search?query=${encodeURIComponent(value)}`);
            
            let isValid = false;
            let standardName = value;

            if (isGitHub && !PRODUCTION_API_URL) {
                // Mock validation for GitHub Pages demo
                const mockKnown = ['aspirin', 'warfarin', '阿斯匹靈', '華法林', 'sildenafil', 'nitroglycerin', '威而鋼', '硝化甘油', 'ibuprofen', 'lithium', '伊普', '鋰鹽', 'statin', 'grapefruit', '史他汀', '葡萄柚'];
                isValid = mockKnown.some(k => value.toLowerCase().includes(k.toLowerCase()));
                standardName = value;
            } else {
                const response = await fetch(apiUrl);
                if (response.ok) {
                    const data = await response.json();
                    // Validation criteria:
                    // 1. Generic name MUST exist
                    // 2. If it's the SAME as query, it's only valid if we also have SMILES (molecular data)
                    //    OR if it's found in our known mock list (for demo)
                    if (data.generic_name) {
                        isValid = true;
                        standardName = data.generic_name;
                        // Save ZH name for tag rendering
                        if (data.zh_name) {
                            drugDisplayNames[standardName] = `${data.zh_name} (${standardName})`;
                        } else {
                            drugDisplayNames[standardName] = standardName;
                        }
                    }
                }
            }

            if (isValid) {
                drugs.push(standardName); // Use the standard name for consistency
                renderTags();
                drugInput.value = '';
            } else {
                alert(`查無此藥品: "${value}"\n請確認藥品名稱輸入是否正確。`);
            }
        } catch (error) {
            console.error('Validation failed', error);
            alert('驗證連線失敗，請稍後再試');
        } finally {
            addBtn.disabled = false;
            addBtn.innerText = '新增藥品';
            analyzeBtn.disabled = drugs.length < 1;
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
            const displayName = drugDisplayNames[drug] || drug;
            tag.innerHTML = `
                ${displayName}
                <span class="remove-btn" onclick="removeDrug(${index})">×</span>
            `;
            drugListContainer.appendChild(tag);
        });
    }

    window.removeDrug = (index) => {
        drugs.splice(index, 1);
        renderTags();
        analyzeBtn.disabled = drugs.length < 1;
    };

    // --- Analysis ---
    analyzeBtn.addEventListener('click', async () => {
        analyzeBtn.disabled = true;
        analyzeBtn.innerText = '正在分析中...';
        
        // --- Deployment Config ---
        const isGitHub = window.location.hostname.includes('github.io');
        
        if (isGitHub) {
            const badge = document.getElementById('demo-badge');
            if (badge) badge.classList.add('active');
        }
        
        try {
            let data;
            const selectedHealthFoods = Array.from(document.querySelectorAll('#health-food-list input:checked')).map(cb => cb.value);

            if (isGitHub && !PRODUCTION_API_URL) {
                // Simulated API call for Demo
                await new Promise(resolve => setTimeout(resolve, 2000));
                data = getSimulatedResult(drugs);
            } else {
                // Real API call (Local or Remote)
                const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
                const baseApiUrl = isLocal ? '/api' : (PRODUCTION_API_URL || '/api');
                
                // 1. 基本藥物交互分析
                const response = await fetch(`${baseApiUrl}/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ drugs })
                });
                data = await response.json();

                // 2. MCP 擴充請求 (並行發送)
                const mcpPromises = [];

                if (selectedHealthFoods.length > 0) {
                    mcpPromises.push(
                        fetch(`${baseApiUrl}/mcp/health-food-check`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ drugs, health_foods: selectedHealthFoods })
                        }).then(async res => {
                            if (!res.ok) throw new Error(`HTTP ${res.status}`);
                            data.health_food_alerts = await res.json();
                        }).catch(e => {
                            console.error("MCP Health Food Check Failed:", e);
                            data.health_food_alerts = { results: [{ raw_text: "⚠️ 無法取得保健品詳細資料。這可能是因為 MCP 伺服器正在背景下載 TFDA 資料庫（首次連線約需 1-2 分鐘），或是連線逾時。" }] };
                        })
                    );
                }


                await Promise.all(mcpPromises);
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
        const normalized = drugList.map(d => d.toLowerCase());
        
        // Define mock cases
        const cases = [
            {
                drugs: ['aspirin', 'warfarin', '阿斯匹靈', '華法林'],
                result: {
                    overall_level: 'red',
                    drug_a_zh: '阿斯匹靈', drug_a_input: 'Aspirin',
                    drug_b_zh: '華法林', drug_b_input: 'Warfarin',
                    level: 'red',
                    description: '嚴重出血風險顯著增加，包括腸胃道出血和腦內出血。',
                    mechanism: '兩者皆具抗凝血/抗血小板作用，併用會產生加成效應。',
                    ai_details: {
                        score: 92,
                        shap: { 'logp': 0.45, 'mw': 0.32, 'tpsa': 0.15 }
                    }
                }
            },
            {
                drugs: ['sildenafil', 'nitroglycerin', '威而鋼', '硝化甘油'],
                result: {
                    overall_level: 'red',
                    drug_a_zh: '威而鋼', drug_a_input: 'Sildenafil',
                    drug_b_zh: '硝化甘油', drug_b_input: 'Nitroglycerin',
                    level: 'red',
                    description: '可能導致嚴重的低血壓，甚至致命。',
                    mechanism: '兩者皆會增加單氧化氮 (NO)，導致血管劇烈擴張。',
                    ai_details: {
                        score: 98,
                        shap: { 'logp': 0.55, 'mw': 0.35, 'tpsa': 0.08 }
                    }
                }
            },
            {
                drugs: ['ibuprofen', 'lithium', '伊普', '鋰鹽'],
                result: {
                    overall_level: 'red',
                    drug_a_zh: '伊普', drug_a_input: 'Ibuprofen',
                    drug_b_zh: '鋰鹽', drug_b_input: 'Lithium',
                    level: 'red',
                    description: '可能導致鋰鹽中毒，影響腎功能。',
                    mechanism: 'NSAIDs 會減少前列腺素合成，進而減少腎臟對鋰的排泄。',
                    ai_details: {
                        score: 85,
                        shap: { 'logp': 0.42, 'mw': 0.28, 'tpsa': 0.15 }
                    }
                }
            },
            {
                drugs: ['statin', 'grapefruit', '史他汀', '葡萄柚'],
                result: {
                    overall_level: 'yellow',
                    drug_a_zh: '史他汀類藥物', drug_a_input: 'Statin',
                    drug_b_zh: '葡萄柚汁', drug_b_input: 'Grapefruit Juice',
                    level: 'yellow',
                    description: '增加藥物血中濃度，可能增加肌肉痠痛風險。',
                    mechanism: '葡萄柚成分會抑制 CYP3A4 酵素，延緩某些史他汀類藥物的代謝。',
                    ai_details: {
                        score: 65,
                        shap: { 'logp': 0.52, 'mw': 0.12, 'tpsa': 0.01 }
                    }
                }
            }
        ];

        let foundPairs = [];
        let maxLevel = 'green';

        // Check for matches
        for (let i = 0; i < normalized.length; i++) {
            for (let j = i + 1; j < normalized.length; j++) {
                const drugA = normalized[i];
                const drugB = normalized[j];

                const match = cases.find(c => 
                    (c.drugs.some(d => drugA.includes(d)) && c.drugs.some(d => drugB.includes(d)))
                );

                if (match) {
                    foundPairs.push(match.result);
                    if (match.result.level === 'red') maxLevel = 'red';
                    else if (match.result.level === 'yellow' && maxLevel !== 'red') maxLevel = 'yellow';
                }
            }
        }

        if (foundPairs.length > 0) {
            return {
                overall_level: maxLevel,
                disclaimer: '免責聲明：此為展示模式，模擬分析結果僅供參考。若需精確分析，請於本地環境執行。',
                pair_results: foundPairs.map(p => ({
                    drug_a_zh: p.drug_a_zh, drug_a_input: p.drug_a_input,
                    drug_b_zh: p.drug_b_zh, drug_b_input: p.drug_b_input,
                    level: p.level,
                    reasons: [{ description: p.description, mechanism: p.mechanism }],
                    ai_details: p.ai_details
                }))
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
                        <path d="M7 12.5L10 15.5L17 8.5" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>`,
                'unknown_drug': `
                    <svg class="status-svg-flat" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="11" fill="#64748b"/>
                        <path d="M12 17V17.01M12 14C12 14 12 12.5 13 11.5C14 10.5 14 9.5 14 8.5C14 7.39543 13.1046 6.5 12 6.5C10.8954 6.5 10 7.39543 10 8.5" stroke="white" stroke-width="2.5" stroke-linecap="round"/>
                    </svg>`
            };
            iconContainer.innerHTML = svgMap[riskLevel] || svgMap['green'];
        }
        
        // Update Text
        if (statusText) statusText.innerText = ''; 
        if (statusSubtext) {
            if (data.overall_level === 'green') {
                statusSubtext.innerText = '您的用藥目前看起來非常安全。';
            } else if (data.overall_level === 'unknown_drug') {
                statusSubtext.innerText = '部分藥品在資料庫中查無資料，建議諮詢醫師。';
            } else {
                statusSubtext.innerText = '偵測到潛在交互作用，建議諮詢醫師或藥師。';
            }

            // 新增 MCP 擴充警示文字
            if (data.health_food_alerts && data.health_food_alerts.results && data.health_food_alerts.results.length > 0) {
                statusSubtext.innerHTML += `<br><span class="warning-text-large" style="color:#f59e0b !important; font-size:0.95rem !important; font-weight:normal !important; display:block !important; margin-top:10px !important;">【重要交互作用警示】：偵測到您選擇的保健品與藥物可能有潛在關聯。</span>`;
            }
        }
        
        document.getElementById('disclaimer-text').innerText = data.disclaimer;

        detailsContainer.innerHTML = '';
        detailsContainer.className = `detail-container view-${currentView}`; // Keep this line

        if ((!data.pair_results || data.pair_results.length === 0) && !data.health_food_alerts) {
            detailsContainer.innerHTML = '<div class="glassmorphism brand-shadow" style="padding: 2rem; text-align: center; color: var(--text-muted);"><p>未偵測到顯著的交互作用。</p></div>';
            if (window.lucide) {
                window.lucide.createIcons();
            }
            return;
        }

        // --- 渲染健康食品分析結果 ---
        if (data.health_food_alerts && data.health_food_alerts.results) {
            data.health_food_alerts.results.forEach(hf => {
                if (hf.raw_text) {
                    const div = document.createElement('div');
                    div.className = 'detail-item mcp-extension-item';
                    div.innerHTML = `
                        <div class="extension-badge"><i data-lucide="leaf"></i> 保健品資訊 (TFDA)</div>
                        <div class="reason-block">
                            <div style="white-space: pre-wrap; font-size: 0.9rem; line-height: 1.5; color: var(--text-color);">${hf.raw_text}</div>
                        </div>
                    `;
                    detailsContainer.appendChild(div);
                } else if (hf.results && hf.results.length > 0) {
                    const item = hf.results[0];
                    const div = document.createElement('div');
                    div.className = 'detail-item mcp-extension-item';
                    div.innerHTML = `
                        <div class="extension-badge"><i data-lucide="leaf"></i> 保健品分析</div>
                        <div class="detail-header">
                            <div class="pair-names">${item.product_name || '未知保健品'}</div>
                        </div>
                        <div class="reason-block">
                            <p><strong>保健功效：</strong>${item.health_benefit || '尚無資料'}</p>
                            <p class="mechanism"><strong>注意事項：</strong>${item.warnings || '請諮詢專業人員'}</p>
                        </div>
                    `;
                    detailsContainer.appendChild(div);
                }
            });
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

            const severityClassMap = { 'red': 'high', 'yellow': 'medium', 'green': 'low', 'unknown_drug': 'unknown' };
            const severityClass = severityClassMap[res.level] || 'low';
            
            const imgNameMap = { 'red': '紅燈', 'yellow': '黃燈', 'green': '綠燈', 'unknown_drug': '紅燈' }; // Use red or neutral? Let's use red for warning or neutral
            const imgName = imgNameMap[res.level] || '綠燈';
            
            // If unknown_drug, don't show the traffic light image or show a special placeholder
             const trafficHtml = res.level === 'unknown_drug' 
                ? `<div class="unknown-placeholder"><i data-lucide="help-circle"></i></div>`
                : `<img src="${imgName}.webp" class="detail-traffic-img" alt="${imgName}">`;

            const nameA = res.drug_a_zh === res.drug_a_input ? res.drug_a_zh : `${res.drug_a_zh} (${res.drug_a_input})`;
            const nameB = res.drug_b_zh === res.drug_b_input ? res.drug_b_zh : `${res.drug_b_zh} (${res.drug_b_input})`;

            div.innerHTML = `
                <div class="detail-header">
                    <div class="pair-names">
                        <div class="pill-3d"></div>
                        ${nameA} + ${nameB}
                    </div>
                    <div class="traffic-image-box">
                        ${trafficHtml}
                    </div>
                </div>
                ${reasonsHtml}
                ${(res.ai_details || (res.reasons.find(r => r.ai_details)?.ai_details)) ? renderAIInsight(res.ai_details || res.reasons.find(r => r.ai_details).ai_details, res.level) : ''}
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

    /**
     * Render AI Insight Block with SHAP bars
     * Enhanced with visibility rules and property explanations
     */
    function renderAIInsight(ai, riskLevel) {
        if (!ai) return '';
        
        // --- 1. AI 預測風險說明 ---
        // 修正分數顯示：後端傳回的是 0-100 的數值，不應再乘以 100 如果它已經是百分比量級
        // 在 main.py/core 中分數已經是 np.clip(raw_score, 0, 100)
        let displayScore = ai.score;
        if (displayScore > 0 && displayScore <= 1) displayScore *= 100;
        if (displayScore > 100) displayScore = 100; // 安全機制

        const scoreExplanation = `
            <div class="ai-explanation-mini">
                <i data-lucide="info" style="width:12px;height:12px"></i>
                數值源自 AI 模型對分子結構（如親脂性、電解質平衡）與藥理相似度的綜合運算。
            </div>
        `;

        // --- 2. SHAP 橫條圖顯示邏輯 ---
        // 只有在高風險 (red) 且 視圖為醫師 (doctor) 時才顯示專業資料
        let shapHtml = '';
        if (currentView === 'doctor' && riskLevel === 'red') {
            const featureNamesZh = {
                'logp': '親脂性 (LogP)',
                'mw': '分子量 (MW)',
                'tpsa': '極性表面積 (TPSA)',
                'h_donors': '氫鍵供體',
                'h_acceptors': '氫鍵受體',
                'rotatable_bonds': '可旋轉鍵',
                'lipinski_violations': '利平斯基規則違規'
            };

            const featureDesc = {
                'logp': '影響藥物在體內組織的分配與生物利用度。',
                'mw': '影響藥物穿透細胞膜的能力。',
                'tpsa': '與藥物穿透血腦屏障的能力高度相關。',
                'lipinski_violations': '違反該規則可能代表藥物在人體內的口服吸收不佳。'
            };

            let shapItemsRaw = [];
            if (Array.isArray(ai.shap_summary)) {
                shapItemsRaw = ai.shap_summary.map(item => ({
                    feature: item.feature,
                    contribution: item.contribution
                }));
            } else if (ai.shap) {
                shapItemsRaw = Object.entries(ai.shap).map(([key, val]) => ({
                    feature: key,
                    contribution: val
                }));
            }

            if (shapItemsRaw.length > 0) {
                const shapItems = shapItemsRaw.map(item => {
                    const val = item.contribution;
                    const isPositive = val > 0;
                    const absVal = Math.abs(val);
                    const percentage = Math.min(absVal * 5, 100); // 調整比例尺
                    
                    const nameZh = featureNamesZh[item.feature] || item.feature;
                    const desc = featureDesc[item.feature] || '';

                    return `
                        <div class="shap-item">
                            <div class="shap-label">
                                <span class="feature-name">${nameZh}</span>
                                <span class="shap-impact ${isPositive ? 'positive' : 'negative'}">
                                    ${isPositive ? '+' : '-'}${absVal.toFixed(2)}
                                </span>
                            </div>
                            <div class="shap-bar-bg">
                                <div class="shap-bar-fill ${isPositive ? 'positive' : 'negative'}" style="width: ${percentage}%"></div>
                            </div>
                            ${desc ? `<div class="feature-desc">${desc}</div>` : ''}
                        </div>
                    `;
                }).join('');

                shapHtml = `
                    <div class="shap-section">
                        <div class="shap-title"><i data-lucide="bar-chart-3"></i> 結構屬性貢獻分析 (僅限醫師參考)</div>
                        <div class="shap-container">
                            ${shapItems}
                        </div>
                    </div>
                `;
            }
        }

        return `
            <div class="ai-insight-block">
                <div class="ai-header">
                    <div class="ai-badge">
                        <i data-lucide="cpu"></i> Powered by MedSafe AI
                    </div>
                    <div class="ai-score-label">
                        AI 預測風險: ${displayScore.toFixed(1)}%
                    </div>
                </div>
                ${scoreExplanation}
                ${shapHtml}
            </div>
        `;
    }
});
