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
        # Custom CSS for styling
    custom_css = """
    :root {
        --primary-50: #e3f2fd; /* Lightest blue */
        --primary-100: #bbdefb;
        --primary-200: #90caf9;
        --primary-300: #64b5f6;
        --primary-400: #42a5f5;
        --primary-500: #2196f3; /* Main blue */
        --primary-600: #1e88e5;
        --primary-700: #1976d2;
        --primary-800: #1565c0;
        --primary-900: #0d47a1; /* Darkest blue */
        --secondary-500: #4a7a9e; /* Complementary blue */
        --text-color: #2c3e50; /* Darker text for contrast */
        --text-color-light: #ecf0f1; /* Light text for dark backgrounds */
        --background-color: #f0f8ff; /* Very light blue background */
        --panel-background-color: #ffffff; /* White for content panels */
        --border-color: #90caf9; /* Light blue border */
        --shadow-color: rgba(33, 150, 243, 0.2); /* Blue shadow */
    }

    body {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }

    .gradio-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: var(--background-color) !important;
    }

    #main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background-color: var(--panel-background-color);
        border-radius: 8px;
        box-shadow: 0 4px 12px var(--shadow-color);
        border: 1px solid var(--border-color);
    }

    #title {
        text-align: center;
        margin-bottom: 10px;
        color: var(--primary-800);
    }

    #subtitle {
        text-align: center;
        color: var(--primary-600);
        margin-bottom: 30px;
        font-size: 16px;
    }

    #upload-row {
        margin-bottom: 20px;
    }

    #try-on-btn {
        background: linear-gradient(45deg, var(--primary-600), var(--primary-800)) !important;
        border: none !important;
        color: var(--text-color-light) !important;
        font-size: 18px;
        font-weight: bold;
        padding: 12px 30px;
        border-radius: 25px;
        margin: 20px auto;
        display: block;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    #try-on-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px var(--shadow-color);
    }

    /* Input fields and labels */
    .gr-text-input, .gr-textbox, .gr-image-label {
        border-color: var(--border-color) !important;
        color: var(--text-color) !important;
        background-color: var(--panel-background-color) !important;
    }

    .gr-box, .gr-image-container, .gr-file-container {
        border: 1px solid var(--border-color) !important;
        background-color: var(--panel-background-color) !important;
    }
    
    .gradio-container h2 { /* Headers in Gradio components */
        color: var(--primary-700) !important;
    }

    .gradio-container p { /* Paragraph text */
        color: var(--text-color) !important;
    }

    /* Style for the API key input specifically */
    .gradio-container label.gr-form-label {
        color: var(--primary-700) !important;
    }

    /* Status text field */
    .gradio-container #component-root > .gr-block.gr-is-input > label > .gr-form-label {
        color: var(--primary-700) !important;
    }

    /* For links within the UI */
    a {
        color: var(--primary-700) !important;
    }
    a:hover {
        color: var(--primary-900) !important;
    }

    /* File upload area text */
    .gr-image-label > div:first-child {
        color: var(--primary-600) !important;
    }
    """
    
    with gr.Blocks(css=custom_css, title="nano banana tryon") as interface:
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
                    label="Status",
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
        
        # Add examples section
        gr.HTML("""
            <div style="margin-top: 30px; padding: 20px;">
                <h3>💡 Tips for Best Results:</h3>
                <ul style="text-align: left; margin: 10px 0;">
                    <li>Get your free Gemini API key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></li>
                    <li>Use clear, well-lit photos of yourself</li>
                    <li>Choose clothing images with good visibility of the garment</li>
                    <li>Avoid cluttered backgrounds when possible</li>
                    <li>Make sure both images are high quality</li>
                </ul>
            </div>
        """)
    
    return interface

if __name__ == "__main__":
    # Create and launch the interface
    demo = create_interface()
    demo.launch()
