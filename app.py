from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont
import qrcode
import base64
import io
import vobject

app = Flask(__name__)

# Define positioning constants for business card elements (values are percentages of card dimensions)
# These values are carefully chosen to match the template design and ensure proper alignment
TEXT_X_OFFSET = 0.15  # Distance from left edge for text elements
NAME_Y_POS = 0.30    # Vertical position for name
PHONE_Y_POS = 0.45   # Vertical position for phone number
EMAIL_Y_POS = 0.55   # Vertical position for email
QR_X_POS = 0.61      # Horizontal position for QR code
QR_Y_POS = 0.36      # Vertical position for QR code

def generate_vcard(name, email, phone):
    """
    Creates a vCard format contact card from user information
    This allows the QR code to be scanned directly into phone contacts
    """
    vcard = vobject.vCard()
    vcard.add('fn').value = name
    vcard.add('email').value = email
    vcard.add('tel').value = phone
    return vcard.serialize()

def generate_qr_code(vcard_data):
    """
    Generates a QR code containing the vCard data
    Configures QR code parameters for optimal scanning on most devices
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(vcard_data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def create_business_card(name, email, phone, debug=False):
    """
    Main function to generate the business card image
    Combines template, user information, and QR code into final design
    
    Parameters:
    - name, email, phone: User contact information
    - debug: If True, shows alignment guides for template development
    """
    # Load and prepare the base template
    template = Image.open('static/template.png')
    draw = ImageDraw.Draw(template)
    
    # Configure text styling with professional font
    try:
        font = ImageFont.truetype("Arial", 25)  # Standard business card font size
    except IOError:
        font = ImageFont.load_default()  # Fallback to system font if Arial unavailable
    
    # Calculate positioning based on template dimensions
    width, height = template.size
    x_offset = int(width * TEXT_X_OFFSET)
    name_y = int(height * NAME_Y_POS)
    phone_y = int(height * PHONE_Y_POS)
    email_y = int(height * EMAIL_Y_POS)
    
    # Set text color to match template design
    text_color = 'rgb(0,0,0)'  # Black text for professional appearance
    
    # Calculate text dimensions for vertical centering
    name_bbox = draw.textbbox((0, 0), name, font=font)
    email_bbox = draw.textbbox((0, 0), email, font=font)
    phone_bbox = draw.textbbox((0, 0), phone, font=font)
    
    # Place text elements with vertical centering
    draw.text((x_offset, name_y - name_bbox[3]/2), name, font=font, fill=text_color)
    draw.text((x_offset, phone_y - phone_bbox[3]/2), phone, font=font, fill=text_color)
    draw.text((x_offset, email_y - email_bbox[3]/2), email, font=font, fill=text_color)
    
    # Generate and position QR code
    qr_size = int(height * 0.4)  # QR code sized for easy scanning
    vcard_data = generate_vcard(name, email, phone)
    qr_image = generate_qr_code(vcard_data).resize((qr_size, qr_size))
    
    # Position QR code with white background for clarity
    qr_x = int(width * QR_X_POS)
    qr_y = int(height * QR_Y_POS)
    white_bg = Image.new('RGB', (qr_size + 20, qr_size + 20), 'white')
    template.paste(white_bg, (qr_x - 10, qr_y - 10))
    template.paste(qr_image, (qr_x, qr_y))
    
    if debug:
        # Add visual guides for template development and testing
        debug_color = 'rgba(255, 0, 0, 128)'  # Semi-transparent red
        
        # Center alignment guides
        draw.line([(width/2, 0), (width/2, height)], fill=debug_color, width=1)
        draw.line([(0, height/2), (width, height/2)], fill=debug_color, width=1)
        
        # Text anchor points for alignment verification
        point_size = 5
        for y in [name_y, phone_y, email_y]:
            draw.ellipse([(x_offset-point_size, y-point_size), 
                         (x_offset+point_size, y+point_size)], 
                        fill=debug_color)
    
    return template

# Flask routes for web interface
@app.route('/', methods=['GET'])
def index():
    """Displays the main page with the card generation form"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_card():
    """
    Handles form submission, generates card, and returns it for display
    Converts the image to base64 for embedding in HTML
    """
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    debug = request.form.get('debug', False)
    
    card = create_business_card(name, email, phone, debug=debug)
    
    buffered = io.BytesIO()
    card.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return render_template('index.html', card_image=img_str)

if __name__ == '__main__':
    app.run(debug=True) 