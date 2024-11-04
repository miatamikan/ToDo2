// タスクジャンプ機能の実装
document.addEventListener('DOMContentLoaded', function() {
    // URLからハッシュを取得
    const hash = window.location.hash;
    if (hash) {
        // ハッシュからtask-を除いたIDを取得
        const taskId = hash.replace('#task-', '');
        const element = document.getElementById(`task-${taskId}`);
        if (element) {
            // スムーズスクロールを実行
            setTimeout(() => {
                element.scrollIntoView({ behavior: 'smooth' });
                // ハイライト効果を追加
                element.classList.add('highlight');
                // 3秒後にハイライトを消す
                setTimeout(() => {
                    element.classList.remove('highlight');
                }, 3000);
            }, 100);
        }
    }

    // タスクリンクのクリックイベントハンドラ
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('copy-task-link') || 
            e.target.parentElement.classList.contains('copy-task-link')) {
            e.preventDefault();
            const taskId = e.target.closest('.task-item').id;
            const fullUrl = window.location.origin + window.location.pathname + '#' + taskId;
            
            // クリップボードにURLをコピー
            navigator.clipboard.writeText(fullUrl).then(() => {
                // コピー成功時の視覚的フィードバック
                const tooltip = document.createElement('div');
                tooltip.className = 'copy-tooltip';
                tooltip.textContent = 'URLをコピーしました！';
                e.target.closest('.task-item').appendChild(tooltip);
                
                // 1秒後にツールチップを消す
                setTimeout(() => {
                    tooltip.remove();
                }, 1000);
            }).catch(err => {
                console.error('クリップボードへのコピーに失敗しました:', err);
                alert('URLのコピーに失敗しました。');
            });
        }
    });
});