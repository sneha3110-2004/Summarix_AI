document.addEventListener('DOMContentLoaded', () => {
    // Theme & Search Logic
    const theme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme);

    window.toggleTheme = () => {
        const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    };

    window.filterCards = () => {
        const q = document.getElementById('neuralSearch').value.toLowerCase();
        document.querySelectorAll('.summary-card').forEach(card => {
            card.style.display = card.getAttribute('data-filename').includes(q) ? 'flex' : 'none';
        });
    };

    // File Preview & Upload
    window.previewFile = () => {
        const file = document.getElementById('pdfInput').files[0];
        if (file) {
            document.getElementById('previewName').innerText = file.name;
            document.getElementById('filePreview').style.display = 'flex';
            document.getElementById('initBtn').style.display = 'block';
            document.getElementById('fileStatus').style.display = 'none';
        }
    };

    window.processFile = async () => {
        const formData = new FormData();
        formData.append('file', document.getElementById('pdfInput').files[0]);
        document.getElementById('loading').style.display = 'block';
        const res = await fetch('/upload', { method: 'POST', body: formData });
        if (res.ok) window.location.reload();
    };

    // Neural Chat Logic
    window.handleChat = async (event, paperId) => {
        if (event.key === 'Enter') {
            const question = event.target.value;
            const chatDisplay = document.getElementById(`chat-${paperId}`);
            chatDisplay.innerHTML += `<p class="user-msg"><b>You:</b> ${question}</p>`;
            event.target.value = '';

            const res = await fetch('/chat_query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paper_id: paperId, question: question })
            });
            const data = await res.json();
            chatDisplay.innerHTML += `<p class="ai-msg"><b>SUMMaRIX:</b> ${data.answer}</p>`;
            chatDisplay.scrollTop = chatDisplay.scrollHeight;
        }
    };
});