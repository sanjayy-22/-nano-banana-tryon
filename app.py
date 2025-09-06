import gradio as gr
import google.generativeai as genai
import os
from PIL import Image
import io
import base64
import tempfile

# Configure Gemini API - will be set by user input

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def try_on_clothes(user_photo, clothing_photo, api_key):
    """
    Process the virtual try-on using Gemini 2.5 Flash Image API
    """
    if user_photo is None or clothing_photo is None:
        return None, gr.File(visible=False), "Please upload both images."
    
    if not api_key or api_key.strip() == "":
        return None, gr.File(visible=False), "❌ Please enter your Gemini API key."
    
    try:
        # Configure Gemini with user's API key
        genai.configure(api_key=api_key.strip())
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # Prepare the prompt
        prompt = """Replace the clothes worn by the person in the first image with the outfit shown in the second image. Make sure the fit looks natural, realistic, and consistent with the user's body pose, lighting, and perspective. Do not alter the person's face, skin, or background."""
        
        # Convert images to the format expected by Gemini
        user_img_data = {
            'mime_type': 'image/png',
            'data': encode_image_to_base64(user_photo)
        }
        
        clothing_img_data = {
            'mime_type': 'image/png', 
            'data': encode_image_to_base64(clothing_photo)
        }
        
        # Generate the response
        response = model.generate_content([
            prompt,
            user_img_data,
            clothing_img_data
        ])
        
        # Debug: Print response structure
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response)}")
        
        # Extract the generated image
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            print(f"Candidate type: {type(candidate)}")
            print(f"Candidate attributes: {dir(candidate)}")
            
            if hasattr(candidate, 'content') and candidate.content.parts:
                print(f"Number of parts: {len(candidate.content.parts)}")
                for i, part in enumerate(candidate.content.parts):
                    print(f"Part {i} type: {type(part)}")
                    print(f"Part {i} attributes: {dir(part)}")
                    
                    if hasattr(part, 'inline_data') and part.inline_data:
                        print(f"Found inline_data in part {i}")
                        print(f"inline_data type: {type(part.inline_data)}")
                        print(f"inline_data attributes: {dir(part.inline_data)}")
                        
                        try:
                            # Check if data is already bytes or needs decoding
                            if isinstance(part.inline_data.data, bytes):
                                image_data = part.inline_data.data
                                print(f"Data is already bytes, length: {len(image_data)}")
                            else:
                                # Decode the base64 image data
                                image_data = base64.b64decode(part.inline_data.data)
                                print(f"Decoded base64 data, length: {len(image_data)}")
                            
                            # Try to open the image
                            result_image = Image.open(io.BytesIO(image_data))
                            print(f"Successfully opened image: {result_image.mode}, {result_image.size}")
                            
                            # Convert to RGB if necessary
                            if result_image.mode != 'RGB':
                                result_image = result_image.convert('RGB')
                            
                            # Save to temporary file for download
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                            result_image.save(temp_file.name, 'PNG')
                            
                            return result_image, gr.File(value=temp_file.name, visible=True), "✅ Virtual try-on completed successfully!"
                            
                        except Exception as img_error:
                            print(f"Error processing image: {str(img_error)}")
                            print(f"Image data type: {type(image_data)}")
                            print(f"Image data length: {len(image_data) if hasattr(image_data, '__len__') else 'N/A'}")
                            continue
                    elif hasattr(part, 'text') and part.text:
                        print(f"Found text in part {i}: {part.text[:100]}...")
        
        # Check if response has text content
        if hasattr(response, 'text') and response.text:
            print(f"Response text: {response.text[:200]}...")
            return None, gr.File(visible=False), f"API Response: {response.text}"
        
        return None, gr.File(visible=False), "❌ Failed to generate try-on result. Please try again with different images."
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"Virtual try-on error: {e}")
        return None, gr.File(visible=False), error_msg

def create_interface():
    """
    Create the Gradio interface
    """
    # Custom CSS for better visibility and styling
    custom_css = """
    :root {
        --primary-50: #e3f2fd;
        --primary-100: #bbdefb;
        --primary-200: #90caf9;
        --primary-300: #64b5f6;
        --primary-400: #42a5f5;
        --primary-500: #2196f3;
        --primary-600: #1e88e5;
        --primary-700: #1976d2;
        --primary-800: #1565c0;
        --primary-900: #0d47a1;
        --text-dark: #1a1a1a;
        --text-medium: #4a4a4a;
        --text-light: #ffffff;
        --background-light: #f8fbff;
        --background-white: #ffffff;
        --border-light: #e1e8f0;
        --shadow: rgba(25, 118, 210, 0.1);
    }

    /* Main container styling */
    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
        background: linear-gradient(135deg, var(--background-light) 0%, var(--primary-50) 100%) !important;
        color: var(--text-dark) !important;
    }

    /* Main content area */
    #main-container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 30px;
        background-color: var(--background-white);
        border-radius: 16px;
        box-shadow: 0 8px 32px var(--shadow);
        border: 1px solid var(--border-light);
    }

    /* Title and subtitle */
    #title {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: var(--primary-800) !important;
        text-align: center;
        margin-bottom: 8px !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    #subtitle {
        font-size: 1.1rem !important;
        color: var(--primary-600) !important;
        text-align: center;
        margin-bottom: 30px !important;
        font-weight: 500 !important;
    }

    /* Button styling */
    #try-on-btn {
        background: linear-gradient(135deg, var(--primary-600), var(--primary-800)) !important;
        border: none !important;
        color: var(--text-light) !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        padding: 14px 40px !important;
        border-radius: 30px !important;
        margin: 25px auto !important;
        display: block !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(25, 118, 210, 0.3) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    #try-on-btn:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(25, 118, 210, 0.4) !important;
        background: linear-gradient(135deg, var(--primary-700), var(--primary-900)) !important;
    }

    #try-on-btn:active {
        transform: translateY(-1px) !important;
    }

    /* Input field styling */
    .gr-textbox, .gr-textbox input, .gr-textbox textarea {
        border: 2px solid var(--border-light) !important;
        border-radius: 8px !important;
        background-color: var(--background-white) !important;
        color: var(--text-dark) !important;
        font-size: 14px !important;
        transition: border-color 0.3s ease !important;
    }

    .gr-textbox:focus-within {
        border-color: var(--primary-500) !important;
        box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1) !important;
    }

    /* Label styling */
    .gr-form label, .gr-block label, label.gr-form-label {
        color: var(--text-dark) !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
        display: block !important;
    }

    /* Image upload areas */
    .gr-image, .gr-file {
        border: 2px dashed var(--border-light) !important;
        border-radius: 12px !important;
        background-color: var(--background-white) !important;
        transition: border-color 0.3s ease !important;
    }

    .gr-image:hover, .gr-file:hover {
        border-color: var(--primary-300) !important;
    }

    /* File upload text */
    .gr-image .gr-upload-text, .gr-file .gr-upload-text {
        color: var(--text-medium) !important;
        font-size: 14px !important;
    }

    /* Status and result text */
    .gr-textbox .gr-textbox-output, .gr-textbox textarea[readonly] {
        background-color: var(--primary-50) !important;
        color: var(--text-dark) !important;
        font-weight: 500 !important;
    }

    /* Image containers */
    .gr-image img {
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
    }

    /* Info text under inputs */
    .gr-form .gr-info {
        color: var(--text-medium) !important;
        font-size: 13px !important;
        margin-top: 4px !important;
    }

    /* Links */
    a {
        color: var(--primary-700) !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }

    a:hover {
        color: var(--primary-900) !important;
        text-decoration: underline !important;
    }

    /* Tips section */
    .tips-section {
        background-color: var(--primary-50) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-top: 30px !important;
        border-left: 4px solid var(--primary-500) !important;
    }

    .tips-section h3 {
        color: var(--primary-800) !important;
        font-size: 1.2rem !important;
        margin-bottom: 15px !important;
        font-weight: 600 !important;
    }

    .tips-section ul {
        margin: 0 !important;
        padding-left: 20px !important;
    }

    .tips-section li {
        color: var(--text-dark) !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        margin-bottom: 8px !important;
    }

    /* Progress bar */
    .gr-progress {
        background-color: var(--primary-500) !important;
    }

    /* Ensure all text is visible */
    * {
        color: var(--text-dark) !important;
    }

    /* Override any inherited white text */
    .gr-block, .gr-form, .gr-panel {
        color: var(--text-dark) !important;
    }

    /* Make sure button text remains white */
    button, .gr-button {
        color: var(--text-light) !important;
    }

    #try-on-btn * {
        color: var(--text-light) !important;
    }
    """
    
    with gr.Blocks(css=custom_css, title="nano banana tryon", theme=gr.themes.Soft()) as interface:
        gr.HTML("""
            <div id="main-container">
                <h1 id="title">🍌 nano banana tryon</h1>
                <p id="subtitle">Powered by Gemini 2.5 Flash Image</p>
            </div>
        """)
        
        # API Key input
        api_key_input = gr.Textbox(
            label="🔑 Enter Your Gemini API Key",
            placeholder="Enter your Gemini API key here...",
            type="password",
            info="Get your free API key from https://makersuite.google.com/app/apikey"
        )
        
        with gr.Row(elem_id="upload-row"):
            with gr.Column():
                user_photo = gr.Image(
                    label="📸 Upload Your Photo",
                    type="pil",
                    height=300,
                    sources=["upload", "webcam"]
                )
            with gr.Column():
                clothing_photo = gr.Image(
                    label="👔 Upload Clothing Photo", 
                    type="pil",
                    height=300,
                    sources=["upload"]
                )
        
        try_on_btn = gr.Button(
            "✨ Try On",
            elem_id="try-on-btn",
            size="lg"
        )
        
        with gr.Row():
            with gr.Column():
                status_text = gr.Textbox(
                    label="📊 Status",
                    value="Upload both images and click 'Try On' to get started!",
                    interactive=False,
                    lines=2
                )
            
        with gr.Row():
            result_image = gr.Image(
                label="🎭 Virtual Try-On Result",
                type="pil",
                height=400
            )
            
            # Download file
            download_file = gr.File(
                label="📥 Download Result",
                visible=False
            )
        
        # Event handlers
        try_on_btn.click(
            fn=try_on_clothes,
            inputs=[user_photo, clothing_photo, api_key_input],
            outputs=[result_image, download_file, status_text],
            show_progress=True
        )
        
        # Add examples section with proper styling
        gr.HTML("""
            <div class="tips-section">
                <h3>💡 Tips for Best Results:</h3>
                <ul>
                    <li>Get your free Gemini API key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
                    <li>Use clear, well-lit photos of yourself</li>
                    <li>Choose clothing images with good visibility of the garment</li>
                    <li>Avoid cluttered backgrounds when possible</li>
                    <li>Make sure both images are high quality</li>
                    <li>For best results, use images with similar lighting conditions</li>
                </ul>
            </div>
        """)
    
    return interface

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch()
