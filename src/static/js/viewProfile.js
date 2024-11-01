const quotes = [
  "The only way to do great work is to love what you do.",
  "Success is not the key to happiness. Happiness is the key to success.",
  "The only limit to our realization of tomorrow will be our doubts of today.",
  "The only thing we have to fear is fear itself.",
  "The only source of knowledge is experience.",
  "The only true wisdom is in knowing you know nothing.",
  "Believe you can and you're halfway there.",
  "Your limitation—it's only your imagination.",
  "Push yourself, because no one else is going to do it for you.",
  "Great things never come from comfort zones.",
  "Dream it. Wish it. Do it.",
  "Success doesn’t just find you. You have to go out and get it.",
  "The harder you work for something, the greater you’ll feel when you achieve it.",
  "Dream bigger. Do bigger.",
  "Don’t stop when you’re tired. Stop when you’re done.",
  "Wake up with determination. Go to bed with satisfaction.",
  "Do something today that your future self will thank you for.",
  "Little things make big days.",
  "It’s going to be hard, but hard does not mean impossible.",
  "Don’t wait for opportunity. Create it.",
  "Sometimes we’re tested not to show our weaknesses, but to discover our strengths.",
  "The key to success is to start before you are ready.",
  "Dream it. Believe it. Build it.",
  "The future belongs to those who believe in the beauty of their dreams.",
  "It’s not whether you get knocked down, it’s whether you get up.",
  "If you want to achieve greatness stop asking for permission.",
  "You are never too old to set another goal or to dream a new dream.",
  "The only place where success comes before work is in the dictionary.",
  "Don’t be pushed around by the fears in your mind. Be led by the dreams in your heart.",
  "Everything you’ve ever wanted is on the other side of fear.",
  "Opportunities don’t happen. You create them.",
  "Dream bigger than your fears.",
  "Your only limit is you.",
  "Sometimes we’re tested not to show our weaknesses, but to discover our strengths.",
  "Don’t watch the clock; do what it does. Keep going.",
  "Success is what happens after you have survived all your mistakes.",
  "What lies behind us and what lies before us are tiny matters compared to what lies within us.",
  "Act as if what you do makes a difference. It does.",
  "Success usually comes to those who are too busy to be looking for it.",
  "The only way to do great work is to love what you do.",
  "If you can dream it, you can achieve it.",
  "The future depends on what you do today.",
  "Everything you can imagine is real.",
  "Success is not how high you have climbed, but how you make a positive difference to the world.",
  "Believe in yourself and all that you are.",
  "It does not matter how slowly you go as long as you do not stop.",
  "Failure is simply the opportunity to begin again, this time more intelligently.",
  "What we fear doing most is usually what we most need to do.",
  "Don’t count the days, make the days count.",
  "Your time is limited, don’t waste it living someone else’s life.",
  "If you want to lift yourself up, lift up someone else.",
  "You don’t have to be great to start, but you have to start to be great.",
  "It always seems impossible until it’s done.",
  "What we think, we become.",
  "You are never too old to set another goal or to dream a new dream.",
  "Success is not in what you have, but who you are.",
  "Everything has beauty, but not everyone sees it.",
  "Don’t be afraid to give up the good to go for the great.",
  "Believe you can and you’re halfway there.",
  "To be the best, you must be able to handle the worst.",
  "Hardships often prepare ordinary people for an extraordinary destiny.",
  "Keep your face always toward the sunshine—and shadows will fall behind you.",
  "You miss 100% of the shots you don’t take.",
  "The only way to achieve the impossible is to believe it is possible.",
  "Success is walking from failure to failure with no loss of enthusiasm.",
  "What you get by achieving your goals is not as important as what you become by achieving your goals.",
  "The man who moves a mountain begins by carrying away small stones.",
  "Do not wait to strike till the iron is hot, but make it hot by striking.",
  "Success is not just about what you accomplish in your life, it's about what you inspire others to do.",
  "You don’t have to be great to start, but you have to start to be great.",
  "Success is the sum of small efforts, repeated day in and day out.",
  "Don’t be pushed around by the fears in your mind. Be led by the dreams in your heart.",
  "Hardships often prepare ordinary people for an extraordinary destiny.",
  "Keep your face always toward the sunshine—and shadows will fall behind you.",
  "The best way to predict your future is to create it.",
  "Dream big and dare to fail.",
  "Start where you are. Use what you have. Do what you can.",
  "The only limit to our realization of tomorrow is our doubts of today.",
  "What you get by achieving your goals is not as important as what you become by achieving your goals.",
  "Your time is limited, so don’t waste it living someone else’s life.",
  "If you are not willing to risk the usual, you will have to settle for the ordinary.",
  "The only way to do great work is to love what you do.",
  "Success usually comes to those who are too busy to be looking for it.",
  "Believe you can and you're halfway there.",
  "Don’t be afraid to give up the good to go for the great.",
  "What we fear doing most is usually what we most need to do.",
  "If you can dream it, you can achieve it."
];


// Enhanced quote display with animation
function refreshQuote() {
  const quoteElement = document.getElementById('quote');
  quoteElement.style.opacity = '0';
  setTimeout(() => {
    quoteElement.innerHTML = quotes[Math.floor(Math.random() * quotes.length)];
    quoteElement.style.opacity = '1';
  }, 300);
}
refreshQuote();

// UserActivity Score Animation
function updateScore(user_points) {
  let currentScore = 0;
  const targetScore = user_points;
  const animateScore = () => {
    if (currentScore < targetScore) {
      currentScore += 1;
      document.getElementById('activityScore').textContent = currentScore;
      requestAnimationFrame(animateScore);
    }
  };
  animateScore();
}


// Recent UserActivity Feed
async function fetchActivities(page = 1, perPage = 10) {
  const response = await fetch(`/api/v1/recent_activity?page=${page}&per_page=${perPage}`);
  const data = await response.json();
  return data;
}

// Update the activity feed with recent activities
function updateActivities(activities) {
  const feed = document.getElementById('activityFeed');
  feed.innerHTML = '';
  activities.forEach(activity => {
    const item = document.createElement('div');
    item.className = 'flex items-center p-3 hover:bg-gray-50 rounded-lg transition-colors';
    item.innerHTML = `
        <div class="mr-3">
          <span class="text-indigo-600"><i class="fas fa-${activity.type}"></i></span>
        </div>
        <div class="flex-1">
          <p class="text-sm text-gray-800">${activity.text}</p>
          <p class="text-xs text-gray-500">${activity.time}</p>
        </div>
      `;
    feed.appendChild(item);
  });
}

// Pagination
let currentPage = 1;
const perPage = 10;

async function loadPage(page) {
  const { activities, total, pages, current_page, user_points } = await fetchActivities(page, perPage);
  updateActivities(activities);
  updateScore(user_points);
  currentPage = current_page;

  // Update pagination controls
  const paginationContainer = document.getElementById('pagination');
  paginationContainer.innerHTML = '';

  // Previous page button
  if (currentPage > 1) {
    const prevButton = document.createElement('button');
    prevButton.className = 'px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors';
    prevButton.textContent = 'Previous';
    prevButton.onclick = () => loadPage(currentPage - 1);
    paginationContainer.appendChild(prevButton);
  }

  // Page numbers
  for (let i = 1; i <= pages; i++) {
    const pageButton = document.createElement('button');
    pageButton.className = `px-4 py-2 ${i === currentPage ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700'} rounded-lg font-medium hover:bg-gray-200 transition-colors`;
    pageButton.textContent = i;
    pageButton.onclick = () => loadPage(i);
    paginationContainer.appendChild(pageButton);
  }

  // Next page button
  if (currentPage < pages) {
    const nextButton = document.createElement('button');
    nextButton.className = 'px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors';
    nextButton.textContent = 'Next';
    nextButton.onclick = () => loadPage(currentPage + 1);
    paginationContainer.appendChild(nextButton);
  }
}

// Initial load
loadPage(1);

// Time Online Counter
function updateOnlineTime() {
  const start = new Date(localStorage.getItem('sessionStart') || new Date());
  const now = new Date();
  const diff = Math.floor((now - start) / 1000);
  const minutes = Math.floor(diff / 60);
  const seconds = diff % 60;
  document.getElementById('timeOnline').textContent = `${minutes}m ${seconds}s`;
}

if (!localStorage.getItem('sessionStart')) {
  localStorage.setItem('sessionStart', new Date());
}

setInterval(updateOnlineTime, 1000);

function switchTab(tabName) {
    // Update button states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Move highlight
    const highlighter = document.querySelector('.tab-highlight');
    const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    const index = Array.from(activeBtn.parentElement.children).indexOf(activeBtn) - 1;
    highlighter.style.left = `${index * 50 + 2}%`;

    // Update content visibility
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        content.style.transform = 'translateX(100%)';
    });
    const activeContent = document.getElementById(tabName);
    activeContent.classList.add('active');
    activeContent.style.transform = 'translateX(0)';
}

// Initialize the first tab
document.addEventListener('DOMContentLoaded', () => {
    switchTab('assigned');
});

function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablink");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}