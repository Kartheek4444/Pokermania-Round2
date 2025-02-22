// Function to deal cards dynamically
const cards = [
    { name: "A\u2660", image: "images/cards/ace_of_spades.png" },
    { name: "K\u2660", image: "images/cards/king_of_spades.png" },
    { name: "Q\u2660", image: "images/cards/queen_of_spades.png" },
    { name: "J\u2660", image: "images/cards/jack_of_spades.png" },
    { name: "10\u2660", image: "images/cards/10_of_spades.png" },
    { name: "9\u2660", image: "images/cards/9_of_spades.png" },
    { name: "8\u2660", image: "images/cards/8_of_spades.png" },
    { name: "7\u2660", image: "images/cards/7_of_spades.png" },
    { name: "6\u2660", image: "images/cards/6_of_spades.png" },
    { name: "5\u2660", image: "images/cards/5_of_spades.png" },
    { name: "4\u2660", image: "images/cards/4_of_spades.png" },
    { name: "3\u2660", image: "images/cards/3_of_spades.png" },
    { name: "2\u2660", image: "images/cards/2_of_spades.png" },
    // For a 6-player game, ensure you have at least 4 more cards in the deck:
    { name: "A\u2665", image: "images/cards/ace_of_hearts.png" },
    { name: "K\u2665", image: "images/cards/king_of_hearts.png" },
    { name: "Q\u2665", image: "images/cards/queen_of_hearts.png" },
    { name: "J\u2665", image: "images/cards/jack_of_hearts.png" },
];

let stepIndex = 0; // Track the current step
let shuffledCards = []; // Store the shuffled cards globally

function dealCards() {
    // Shuffle the deck
    shuffledCards = cards.sort(() => Math.random() - 0.5);
    // Show the Next button (ensure your HTML has an element with id "nextButton")
    document.getElementById("nextButton").style.display = "block";
    nextStep(); // Start the first step
}

function nextStep() {
    const steps = [
      // Step 1: Display all players' cards
      () => {
        // Player 1
        setCardImage('player1-card1', shuffledCards[0].image);
        setCardImage('player1-card2', shuffledCards[1].image);
        // Player 2
        setCardImage('player2-card1', shuffledCards[2].image);
        setCardImage('player2-card2', shuffledCards[3].image);
        // Player 3
        setCardImage('player3-card1', shuffledCards[4].image);
        setCardImage('player3-card2', shuffledCards[5].image);
        // Player 4
        setCardImage('player4-card1', shuffledCards[6].image);
        setCardImage('player4-card2', shuffledCards[7].image);
        // Player 5
        setCardImage('player5-card1', shuffledCards[8].image);
        setCardImage('player5-card2', shuffledCards[9].image);
        // Player 6
        setCardImage('player6-card1', shuffledCards[10].image);
        setCardImage('player6-card2', shuffledCards[11].image);
      },
      // Step 2: Reveal the first two community cards together
      () => {
        setCardImage('community-card-1', shuffledCards[12].image);
        setCardImage('community-card-2', shuffledCards[13].image);
      },
      // Step 3: Reveal community card 3
      () => {
        setCardImage('community-card-3', shuffledCards[14].image);
      },
      // Step 4: Reveal community card 4
      () => {
        setCardImage('community-card-4', shuffledCards[15].image);
      },
      // Step 5: Reveal community card 5
      () => {
        setCardImage('community-card-5', shuffledCards[16].image);
      },
      // Final Step: Dim the page and show results
      () => {
        dimPage();
        showResults(shuffledCards);
        document.getElementById("nextButton").style.display = "none"; // Hide Next button after final step
      }
    ];
  
    if (stepIndex < steps.length) {
      steps[stepIndex++]();
    }
  }
  
  

// Update the setCardImage function
function setCardImage(cardSlotId, cardImageSrc) {
    const cardSlot = document.getElementById(cardSlotId);
    if (cardSlot) {
        const cardImage = document.createElement('img');
        cardImage.src = cardImageSrc;
        cardImage.alt = cardSlotId;
        cardImage.style.width = "100%";
        cardImage.style.height = "100%";
        cardSlot.innerHTML = '';
        cardSlot.appendChild(cardImage);
    }
}

// Function to dim the page
function dimPage() {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    overlay.style.zIndex = '9999';
    overlay.id = 'overlay';
    document.body.appendChild(overlay);
}

// Function to show results on the page
function showResults(shuffledCards) {
    // Extract cards for each player and the community.
    // Ensure that your deck has at least 17 cards.
    const player1Cards = shuffledCards.slice(0, 2);
    const player2Cards = shuffledCards.slice(2, 4);
    const player3Cards = shuffledCards.slice(4, 6);
    const player4Cards = shuffledCards.slice(6, 8);
    const player5Cards = shuffledCards.slice(8, 10);
    const player6Cards = shuffledCards.slice(10, 12);
    const communityCards = shuffledCards.slice(12, 17);

    // Build community cards HTML
    let communityCardsHTML = '';
    communityCards.forEach(card => {
        communityCardsHTML += `<img src="${card.image}" alt="${card.name}" style="width: 6%; margin: 5px;">`;
    });

    // Create results display with a table for 6 players.
    const resultsDiv = document.createElement('div');
    resultsDiv.style.position = 'fixed';
    resultsDiv.style.top = '50%';
    resultsDiv.style.left = '50%';
    resultsDiv.style.transform = 'translate(-50%, -50%)';
    resultsDiv.style.backgroundColor = '#1f2937';
    resultsDiv.style.color = 'white';
    resultsDiv.style.padding = '20px';
    resultsDiv.style.borderRadius = '10px';
    resultsDiv.style.textAlign = 'center';
    resultsDiv.style.fontSize = '1rem';
    resultsDiv.style.zIndex = '10000';
    resultsDiv.style.width = '80%';
    resultsDiv.style.maxWidth = '800px';
    resultsDiv.style.overflowY = 'auto';

    resultsDiv.innerHTML = `
        <h2>Round Complete!</h2>
        <p>
            <strong style="color: #ffcc00;">Player 1</strong> wins <strong style="color: #ffcc00;">15605 chips</strong> from the pot with a <strong style="color: rgb(255, 0, 0);">Straight</strong>!
        </p>
        <br>
        <h3>Community Cards</h3>
        <div>${communityCardsHTML}</div>
        <h3>Results</h3>
        <table style="width: 80%; margin-top: 20px; border-collapse: collapse; margin-left: auto; margin-right: auto;">
            <thead>
                <tr>
                    <th style="padding: 5px;">Player</th>
                    <th style="padding: 5px; width: 30%;">Player Cards</th>
                    <th style="padding: 5px;">Chips</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 10px; text-align: center;">Player 1</td>
                    <td style="padding: 10px; text-align: center;">
                        <img src="${player1Cards[0].image}" alt="${player1Cards[0].name}" style="width: 22%; margin: 1px;">
                        <img src="${player1Cards[1].image}" alt="${player1Cards[1].name}" style="width: 22%; margin: 1px;">
                    </td>
                    <td style="padding: 10px; text-align: center;">+15605</td>
                </tr>
                <tr>
                    <td style="padding: 10px; text-align: center;">Player 2</td>
                    <td style="padding: 10px; text-align: center;">
                        <img src="${player2Cards[0].image}" alt="${player2Cards[0].name}" style="width: 22%; margin: 1px;">
                        <img src="${player2Cards[1].image}" alt="${player2Cards[1].name}" style="width: 22%; margin: 1px;">
                    </td>
                    <td style="padding: 10px; text-align: center;">-15605</td>
                </tr>
                <tr>
                    <td style="padding: 10px; text-align: center;">Player 3</td>
                    <td style="padding: 10px; text-align: center;">
                        <img src="${player3Cards[0].image}" alt="${player3Cards[0].name}" style="width: 22%; margin: 1px;">
                        <img src="${player3Cards[1].image}" alt="${player3Cards[1].name}" style="width: 22%; margin: 1px;">
                    </td>
                    <td style="padding: 10px; text-align: center;">+5000</td>
                </tr>
                <tr>
                    <td style="padding: 10px; text-align: center;">Player 4</td>
                    <td style="padding: 10px; text-align: center;">
                        <img src="${player4Cards[0].image}" alt="${player4Cards[0].name}" style="width: 22%; margin: 1px;">
                        <img src="${player4Cards[1].image}" alt="${player4Cards[1].name}" style="width: 22%; margin: 1px;">
                    </td>
                    <td style="padding: 10px; text-align: center;">+2000</td>
                </tr>
                <tr>
                    <td style="padding: 10px; text-align: center;">Player 5</td>
                    <td style="padding: 10px; text-align: center;">
                        <img src="${player5Cards[0].image}" alt="${player5Cards[0].name}" style="width: 22%; margin: 1px;">
                        <img src="${player5Cards[1].image}" alt="${player5Cards[1].name}" style="width: 22%; margin: 1px;">
                    </td>
                    <td style="padding: 10px; text-align: center;">-2000</td>
                </tr>
                <tr>
                    <td style="padding: 10px; text-align: center;">Player 6</td>
                    <td style="padding: 10px; text-align: center;">
                        <img src="${player6Cards[0].image}" alt="${player6Cards[0].name}" style="width: 22%; margin: 1px;">
                        <img src="${player6Cards[1].image}" alt="${player6Cards[1].name}" style="width: 22%; margin: 1px;">
                    </td>
                    <td style="padding: 10px; text-align: center;">+1000</td>
                </tr>
            </tbody>
        </table>
        <button onclick="closeResults()" style="margin-top: 20px; padding: 10px 20px; background-color: #ef4444; color: white; border: none; border-radius: 5px;">Close</button>
    `;

    document.body.appendChild(resultsDiv);
}

// Function to close the results and remove the overlay, then redirect
function closeResults() {
    const overlay = document.getElementById('overlay');
    const resultsDiv = document.querySelector('div[style*="position: fixed"]');
    if (overlay) overlay.remove();
    if (resultsDiv) resultsDiv.remove();
    window.location.href = 'play.html';
}

// Call the function to deal cards when the page loads
window.onload = dealCards;
