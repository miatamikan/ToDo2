document.addEventListener('DOMContentLoaded', function() {
    // URLからハッシュを取得してスクロール
    const hash = window.location.hash;
    if (hash) {
        const taskId = hash.replace('#task-', '');
        const element = document.getElementById(`task-${taskId}`);
        if (element) {
            setTimeout(() => {
                element.scrollIntoView({ behavior: 'smooth' });
                element.classList.add('highlight');
                setTimeout(() => {
                    element.classList.remove('highlight');
                }, 3000);
            }, 100);
        }
    }
});

// タスクリンクのクリックイベント処理
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('task-link') || 
        e.target.parentElement.classList.contains('task-link')) {
        e.preventDefault();
        const taskElement = e.target.closest('.task-content');
        if (taskElement) {
            const taskId = taskElement.id;
            const fullUrl = window.location.origin + window.location.pathname + '#' + taskId;
            
            // クリップボードにコピー
            navigator.clipboard.writeText(fullUrl).then(() => {
                const feedback = document.createElement('div');
                feedback.className = 'copy-feedback';
                feedback.textContent = 'URLをコピーしました';
                taskElement.appendChild(feedback);
                
                setTimeout(() => {
                    feedback.remove();
                }, 1000);
            });
        }
    }
});
