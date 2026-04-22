/**
 * vote.js - 在线投票系统前端脚本
 */

// 投票详情页：实时倒计时
(function initCountdown() {
    const el = document.getElementById('countdown');
    if (!el) return;
    const end = new Date(el.dataset.end);
    function update() {
        const diff = end - new Date();
        if (diff <= 0) { el.textContent = '已截止'; return; }
        const d = Math.floor(diff / 86400000);
        const h = Math.floor((diff % 86400000) / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        el.textContent = `${d}天 ${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }
    update();
    setInterval(update, 1000);
})();

// 自动关闭 Alert
(function autoCloseAlerts() {
    setTimeout(() => {
        document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(el => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            bsAlert.close();
        });
    }, 4000);
})();
