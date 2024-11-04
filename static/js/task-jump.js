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
                setTimeout(() => {
                    element.classList.remove('highlight');
                }, 3000);
            }, 100);
        }
    }

    // タスクリンクのクリックイベントハンドラ
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('task-link') || 
            e.target.parentElement.classList.contains('task-link')) {
            e.preventDefault();
            const taskId = e.target.closest('.task-item').id;
            const fullUrl = window.location.origin + window.location.pathname + '#' + taskId;
            
            // クリップボードにURLをコピー
            navigator.clipboard.writeText(fullUrl).then(() => {
                // コピー成功時の視覚的フィードバック
                const feedbackSpan = document.createElement('span');
                feedbackSpan.className = 'copy-feedback';
                feedbackSpan.textContent = 'URLをコピーしました';
                e.target.closest('.task-item').appendChild(feedbackSpan);
                
                setTimeout(() => {
                    feedbackSpan.remove();
                }, 1000);
            });
        }
    });
});
