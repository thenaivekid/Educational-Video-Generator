const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Define initial shape properties
let shape = {
    x: 100,
    y: 100,
    width: 100,
    height: 100,
    angle: 0, // rotation angle in radians
    reflected: false
};

// Function to draw the shape
function drawShape() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(shape.x + shape.width / 2, shape.y + shape.height / 2); // Move to center of shape
    ctx.rotate(shape.angle); // Rotate around center
    if (shape.reflected) ctx.scale(-1, 1); // Reflect horizontally

    ctx.fillStyle = 'blue';
    ctx.fillRect(-shape.width / 2, -shape.height / 2, shape.width, shape.height); // Draw rectangle

    ctx.restore();
}

// Function to translate the shape
function translateShape() {
    shape.x += 10;
    drawShape();
}

// Function to rotate the shape
function rotateShape() {
    shape.angle += Math.PI / 6; // Rotate by 30 degrees
    drawShape();
}

// Function to reflect the shape
function reflectShape() {
    shape.reflected = !shape.reflected; // Toggle reflection
    drawShape();
}

// Initial drawing
drawShape();
