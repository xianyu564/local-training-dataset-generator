import torch
import os
import json
from datetime import datetime

# 设置环境变量以修复 libgomp 警告
os.environ["OMP_NUM_THREADS"] = "1"

# 核心修复：必须在导入 transformers 之前尝试导入 unsloth 以开启优化
if torch.cuda.is_available():
    try:
        import unsloth
        print("Unsloth optimization pre-loaded.")
    except ImportError:
        pass

import gradio as gr
from train import run_training

# Configuration
base_model_path = "unsloth/Qwen2.5-0.5B-Instruct"
lora_path = "lora/qwen2.5-0.5b-lora" 

# Determine device and dtype
if torch.cuda.is_available():
    device = "cuda"
    dtype = torch.float16
else:
    device = "cpu"
    dtype = torch.float32

# Global model/tokenizer for Chat
model = None
tokenizer = None

def load_chat_model(hub_model_id=None):
    global model, tokenizer
    print("Loading model for chat...")
    
    # 检查是否有 GPU
    if not torch.cuda.is_available():
        raise RuntimeError("❌ Chat and Test features require GPU. Please enable GPU in Space settings.")
    
    # 使用 Unsloth 加载模型（与训练时一致）
    from unsloth import FastLanguageModel
    
    max_seq_length = 2048
    dtype_map = None  # Auto detection
    load_in_4bit = True
    
    # 优先级：Hub repo ID > 本地 LoRA > 基础模型
    if hub_model_id:
        print(f"Loading model with LoRA from Hub: {hub_model_id}")
        try:
            model, tokenizer = FastLanguageModel.from_pretrained(
                model_name=hub_model_id,
                max_seq_length=max_seq_length,
                dtype=dtype_map,
                load_in_4bit=load_in_4bit,
            )
            print("✅ LoRA weights loaded from Hub successfully.")
        except Exception as e:
            print(f"❌ Failed to load from Hub: {e}")
            raise RuntimeError(f"Failed to load model from Hub {hub_model_id}: {str(e)}")
    elif os.path.exists(lora_path):
        print(f"Loading model with LoRA from local: {lora_path}")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=lora_path,
            max_seq_length=max_seq_length,
            dtype=dtype_map,
            load_in_4bit=load_in_4bit,
        )
        print("✅ Local LoRA weights loaded successfully.")
    else:
        print(f"LoRA not found at {lora_path}, loading base model")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=base_model_path,
            max_seq_length=max_seq_length,
            dtype=dtype_map,
            load_in_4bit=load_in_4bit,
        )
        print("⚠️ Using base model without LoRA")
    
    # Set to inference mode
    FastLanguageModel.for_inference(model)

def respond(message, history):
    try:
        if model is None:
            load_chat_model()
    except RuntimeError as e:
        return f"❌ {str(e)}"
    
    # 使用 Qwen 的 chat template
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for user_msg, assistant_msg in history:
        messages.append({"role": "user", "content": user_msg})
        messages.append({"role": "assistant", "content": assistant_msg})
    messages.append({"role": "user", "content": message})
    
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response

def start_training_ui(hf_token, repo_id, push_to_hub):
    if not hf_token:
        hf_token = os.getenv("HF_TOKEN")
    
    try:
        result = run_training(
            hf_token=hf_token,
            hub_repo_id=repo_id,
            push_to_hub=push_to_hub,
            export_gguf=True
        )
        return f"✅ {result}"
    except Exception as e:
        return f"❌ Training failed: {str(e)}"

def run_test_inference(hub_model_id=None, upload_repo_id=None):
    """Run inference on all test questions
    
    Args:
        hub_model_id: Optional Hub repo ID to load LoRA from (e.g., 'xianyu564/train-qwen-demo')
        upload_repo_id: Optional Hub repo ID to upload results to (defaults to hub_model_id if not provided)
    """
    try:
        # 如果提供了 hub_model_id 或者模型未加载，则重新加载
        if hub_model_id or model is None:
            load_chat_model(hub_model_id=hub_model_id)
    except RuntimeError as e:
        return str(e)
    
    # 确定上传目标：优先使用 upload_repo_id，其次使用 hub_model_id
    target_repo_id = upload_repo_id or hub_model_id
    
    test_file = "data/test_questions_fullLength.jsonl"
    if not os.path.exists(test_file):
        return "❌ Test file not found: data/test_questions_fullLength.jsonl"
    
    # Load test questions
    test_data = []
    with open(test_file, 'r', encoding='utf-8') as f:
        for line in f:
            test_data.append(json.loads(line))
    
    results = []
    for idx, entry in enumerate(test_data, 1):
        scenario = entry['scenario']
        difficulty = entry['difficulty']
        question_input = entry['input']
        
        # Format prompt based on scenario
        if scenario == 1:
            instruction = "分析以下代码片段，并从资深开发者的角度回答一个典型的初级开发者提问。请包含详细的推理过程。"
        else:
            instruction = "基于提供的代码架构概览，为新需求设计一套技术方案。请包含详细的设计推理过程，并确保方案符合现有架构模式。"
        
        messages = [
            {"role": "system", "content": "你是一位资深的软件工程师，擅长代码分析和架构设计。"},
            {"role": "user", "content": f"{instruction}\n\n{question_input}"}
        ]
        
        # Format with chat template
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Generate response
        try:
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
            
            response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        except Exception as e:
            response = f"❌ Generation error: {str(e)}"
        
        result_text = f"## Question {idx} - Scenario {scenario} - {difficulty}\n\n"
        result_text += f"**Input (first 300 chars):**\n{question_input[:300]}...\n\n"
        result_text += f"**Model Response:**\n{response}\n\n"
        result_text += "-" * 80 + "\n\n"
        
        results.append(result_text)
    
    try:
        # Generate timestamped filename to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"lora/test_results_fullLength_{timestamp}.txt"
        latest_file = "lora/test_results_fullLength_latest.txt"
        
        os.makedirs("lora", exist_ok=True)
        
        # Write to timestamped file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"微调模型测试结果 (完整问题版本) - {timestamp}\n")
            f.write(f"Model source: {hub_model_id if hub_model_id else 'local/base'}\n")
            f.write("=" * 80 + "\n\n")
            for result in results:
                f.write(result)
        
        # Also write to "latest" file for easy access
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"微调模型测试结果 (完整问题版本) - {timestamp}\n")
            f.write(f"Model source: {hub_model_id if hub_model_id else 'local/base'}\n")
            f.write("=" * 80 + "\n\n")
            for result in results:
                f.write(result)
        
        # Try to push to Hub if possible
        upload_msg = ""
        try:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token and target_repo_id:
                from huggingface_hub import HfApi
                api = HfApi()
                print(f"Uploading test results to Hub: {target_repo_id}")
                # Upload both timestamped and latest
                api.upload_file(
                    path_or_fileobj=output_file,
                    path_in_repo=output_file,
                    repo_id=target_repo_id,
                    token=hf_token
                )
                api.upload_file(
                    path_or_fileobj=latest_file,
                    path_in_repo=latest_file,
                    repo_id=target_repo_id,
                    token=hf_token
                )
                upload_msg = f"\n📤 Results uploaded to {target_repo_id}:\n  - {output_file}\n  - {latest_file}"
            elif not hf_token:
                upload_msg = "\n⚠️ Upload skipped: HF_TOKEN not set"
            elif not target_repo_id:
                upload_msg = "\n⚠️ Upload skipped: No repo ID provided"
        except Exception as e:
            upload_msg = f"\n⚠️ Upload failed: {str(e)}"
        
        summary = f"✅ Inference completed!\n"
        summary += f"📁 Saved to:\n  - {output_file} (timestamped)\n  - {latest_file} (latest)\n"
        summary += upload_msg
        summary += f"\n\n{'='*60}\n📊 Results Preview (first 2 questions):\n{'='*60}\n\n"
        
        return summary + "".join(results[:2])  # Show first 2 results
    except Exception as e:
        return f"❌ Failed to save results: {str(e)}\n\nResults preview:\n" + ("".join(results[:2]) if results else "")

# UI
with gr.Blocks() as demo:
    gr.Markdown("# Qwen2.5 Fine-tuning & Chat Demo")
    
    with gr.Tab("💬 Chat"):
        gr.ChatInterface(
            fn=respond,
            title="Qwen2.5 Chat",
            description="Chat with the base or fine-tuned model."
        )
    
    with gr.Tab("🚀 Train"):
        gr.Markdown("### Start Remote Training")
        gr.Info("Note: Training requires a GPU Space. Ensure you have a 'HF_TOKEN' secret set in your Space settings if you want to push to Hub.")
        
        with gr.Row():
            hf_token_input = gr.Textbox(label="HF Token (optional if set in Secrets)", type="password")
            repo_id_input = gr.Textbox(label="Hub Repo ID", value="xianyu564/train-qwen-demo")
        
        push_hub_checkbox = gr.Checkbox(label="Push to Hugging Face Hub (will save to /lora/ folder)", value=True)
        train_button = gr.Button("Start Training", variant="primary")
        output_status = gr.Textbox(label="Status")
        
        train_button.click(
            fn=start_training_ui,
            inputs=[hf_token_input, repo_id_input, push_hub_checkbox],
            outputs=output_status
        )
    
    with gr.Tab("🧪 Test"):
        gr.Markdown("### Run Inference on Test Questions")
        gr.Info("This will run the fine-tuned model on all 10 test questions from data/test_questions_fullLength.jsonl")
        
        with gr.Row():
            hub_model_input = gr.Textbox(
                label="Load Model From (optional)",
                placeholder="e.g., xianyu564/train-qwen-demo",
                info="Leave empty to use local LoRA or base model. Provide Hub repo ID to load trained weights from Hub."
            )
            upload_repo_input = gr.Textbox(
                label="Upload Results To",
                value="xianyu564/train-qwen-demo",
                info="Hub repo ID to upload test results. Results will be saved to lora/ folder."
            )
        
        with gr.Row():
            test_button = gr.Button("Run Test Inference", variant="primary")
            reload_button = gr.Button("🔄 Reload Model from Hub", variant="secondary")
        
        test_output = gr.Textbox(label="Test Results Preview", lines=20)
        
        test_button.click(
            fn=run_test_inference,
            inputs=[hub_model_input, upload_repo_input],
            outputs=test_output
        )
        
        def reload_model(hub_id):
            try:
                global model
                model = None  # Force reload
                load_chat_model(hub_model_id=hub_id if hub_id else None)
                source = hub_id if hub_id else "local/base"
                return f"✅ Model reloaded successfully from {source}"
            except Exception as e:
                return f"❌ Failed to reload model: {str(e)}"
        
        reload_button.click(
            fn=reload_model,
            inputs=[hub_model_input],
            outputs=test_output
        )

if __name__ == "__main__":
    demo.launch()
