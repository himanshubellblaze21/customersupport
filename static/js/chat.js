const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
 
appendPreMessage("Hi there! I'm your personal assistant. ");
appendDealsMessage();

 
function appendPreMessage(text) {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', 'bot');
  const bubble = document.createElement('div');
  bubble.classList.add('bubble');
  bubble.style.textAlign = 'center';
  bubble.textContent = text;
  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
 

function appendDealsMessage() {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', 'bot');

  const bubble = document.createElement('div');
  bubble.classList.add('bubble');
  bubble.style.textAlign = 'center';

  // Container that will hold our two buttons
  const dealsContainer = document.createElement('div');
  dealsContainer.classList.add('deals-container');

  // ► List of (button label, query) pairs:
  const solarQuestions = [
    {
      label: 'How to Clean Solar Panels?',
      query: 'How do I clean my solar panels?'
    },
    {
      label: 'Models & Prices',
      query: 'What solar panel models do you offer, and what are their prices?'
    }
  ];

  // Create each button and attach an event listener
  solarQuestions.forEach(({ label, query }) => {
    const btn = document.createElement('button');
    btn.classList.add('deal-button');
    btn.textContent = label;

    btn.addEventListener('click', () => {
      sendMessage(query);
    });

    dealsContainer.appendChild(btn);
  });

  // Put the container into the bubble, then insert into chat window
  bubble.appendChild(dealsContainer);
  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function sendMessage(textParam) {
  const text = textParam || userInput.value.trim(); 
  if (!text) return;
  appendUserMessage(text);
  if (!textParam) userInput.value = '';
  sendBtn.disabled = true;
 
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: text })
    });
    const data = await res.json();
    await appendBotMessage(data.answer);
  } catch (err) {
    await appendBotMessage('Error: Could not reach server.');
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
  }
}
 
function appendUserMessage(text) {
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', 'user');
  const bubble = document.createElement('div');
  bubble.classList.add('bubble');
  bubble.textContent = text;
  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
 
// async function appendBotMessage(rawText)
 async function appendBotMessage(rawText, showFeedback = true){
  const text = rawText.replace(/^Bot:\s*/i, '').trim();
 
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', 'bot');
  const bubble = document.createElement('div');
  bubble.classList.add('bubble');
  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
 
  const lines = text.split('\n').filter(line => line.trim() !== '');
 
  const ul = document.createElement('ul');
  bubble.appendChild(ul);
 
  for (const line of lines) {
    const li = document.createElement('li');
    ul.appendChild(li);
 
    const cursor = document.createElement('span');
    cursor.classList.add('cursor');
    li.appendChild(cursor);
 
    const tokens = line.split(/(\s+)/);
 
    for (const token of tokens) {
      await new Promise(res => setTimeout(res, 100));
      li.insertBefore(document.createTextNode(token), cursor);
      chatWindow.scrollTop = chatWindow.scrollHeight;
    }
    cursor.remove();
  }
  // appendFeedbackPrompt()
  if (showFeedback) {
    appendFeedbackPrompt();
  }
}



function appendFeedbackPrompt() {
  // 1) Create the outer container (a bot‐style “bubble”)
  const msgDiv = document.createElement('div');
  msgDiv.classList.add('message', 'bot');

  const bubble = document.createElement('div');
  bubble.classList.add('bubble');
  bubble.style.textAlign = 'center';

  // 2) Insert your “Was this helpful? Yes/No” markup
  bubble.innerHTML = `
    <div class="feedback-prompt">
      <span>Was this helpful?</span>
      <button id="feedback-yes">👍</button>
      <button id="feedback-no">👎</button>
    </div>
  `;

  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  // 3) Wire up the click handlers for “Yes” and “No”
  document.getElementById('feedback-yes').addEventListener('click', () => {
    handleFeedback(true);
  });
  document.getElementById('feedback-no').addEventListener('click', () => {
    handleFeedback(false);
  });
}


function handleFeedback(isHelpful) {
  // 1) Locate the feedback‐prompt container
  const promptDiv = document.querySelector('.feedback-prompt');
  if (promptDiv) {
    // 2) Remove its wrapping .message.bot entirely
    const msgDiv = promptDiv.closest('.message.bot');
    if (msgDiv) {
      msgDiv.remove();
    }
  }

  // 3) Now proceed with recording their choice and showing the next message
  if (isHelpful) {
    appendUserMessage('👍');
    appendBotMessage("Great! Glad I could help 😊",false);
  } else {
    appendUserMessage('👎');
    appendBotMessage("Apologies—connecting you to a human agent. For immediate assistance, call +91-98765-43210.",false);
    escalateToHuman();
  }
}


 
document.getElementById('input-area').addEventListener('submit', e => {
  e.preventDefault();
  sendMessage();
});
 
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && document.activeElement === userInput) {
    sendMessage();
  }
});