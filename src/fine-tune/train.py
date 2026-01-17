import os

# Note: Unsloth must be imported before transformers/peft for optimizations.
# To prevent the Space from crashing on CPU-only boot (NotImplementedError),
# we wrap the unsloth import inside the training function.

def run_training(
    model_id="unsloth/Qwen2.5-0.5B-Instruct",
    dataset_path="data/train_dataset_20260117_194659.jsonl",
    output_name="lora/qwen2.5-0.5b-lora",
    hf_token=None,
    push_to_hub=False,
    hub_repo_id="xianyu564/train-qwen-demo", # Default to your repo
    export_gguf=True
):
    from unsloth import FastLanguageModel
    import torch
    from datasets import load_dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from unsloth import is_bfloat16_supported

    # 1. Configuration
    max_seq_length = 2048
    load_in_4bit = True

    # 2. Load Model & Tokenizer
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_id,
        max_seq_length = max_seq_length,
        load_in_4bit = load_in_4bit,
    )

    # 3. Add LoRA weights
    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                          "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 16,
        lora_dropout = 0,
        bias = "none",
        use_gradient_checkpointing = "unsloth",
        random_state = 3407,
        use_rslora = False,
        loftq_config = None,
    )

    # 4. Data Preparation
    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        inputs       = examples["input"]
        outputs      = examples["output"]
        texts = []
        for instruction, input, output in zip(instructions, inputs, outputs):
            text = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{instruction}\n\n{input}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
            texts.append(text)
        return { "text" : texts, }

    if not os.path.exists(dataset_path):
        import glob
        # Specifically search for training datasets
        files = glob.glob("data/train_dataset*.jsonl")
        if files:
            # Pick the latest or first one
            dataset_path = sorted(files)[-1] 
            print(f"Dataset not found at default path, using: {dataset_path}")
        else:
            # Fallback to any jsonl if specific train one not found
            files = glob.glob("data/*.jsonl")
            if files:
                dataset_path = files[0]
                print(f"No train_dataset*.jsonl found, using: {dataset_path}")
            else:
                raise FileNotFoundError(f"No dataset found at {dataset_path} or in data/*.jsonl")

    dataset = load_dataset("json", data_files={"train": dataset_path}, split="train")
    dataset = dataset.map(formatting_prompts_func, batched = True,)

    # 5. Trainer Setup
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        dataset_num_proc = 2,
        packing = False,
        args = TrainingArguments(
            per_device_train_batch_size = 2,
            gradient_accumulation_steps = 4,
            warmup_steps = 5,
            max_steps = 60,
            learning_rate = 2e-4,
            fp16 = not is_bfloat16_supported(),
            bf16 = is_bfloat16_supported(),
            logging_steps = 1,
            optim = "adamw_8bit",
            weight_decay = 0.01,
            lr_scheduler_type = "linear",
            seed = 3407,
            output_dir = "lora/outputs", # Save logs/checkpoints to lora/outputs
            report_to = "tensorboard",
            logging_dir = "lora/logs",    # Explicitly set logging directory
        ),
    )

    # 6. Train
    print("Starting training...")
    trainer.train()

    # 7. Save and Push
    os.makedirs(os.path.dirname(output_name), exist_ok=True)
    print(f"Saving model to {output_name}...")
    model.save_pretrained(output_name)
    tokenizer.save_pretrained(output_name)

    if push_to_hub and hub_repo_id:
        from huggingface_hub import HfApi
        api = HfApi()
        
        print(f"Pushing LoRA to Hub: {hub_repo_id}...")
        model.push_to_hub(hub_repo_id, token=hf_token)
        tokenizer.push_to_hub(hub_repo_id, token=hf_token)

        # Upload Training Logs
        if os.path.exists("lora/logs"):
            print("Uploading training logs to Hub...")
            api.upload_folder(
                folder_path="lora/logs",
                path_in_repo="lora/logs",
                repo_id=hub_repo_id,
                token=hf_token
            )
        
        # Upload Training History (trainer_state.json)
        if os.path.exists("lora/outputs"):
            print("Uploading trainer state to Hub...")
            # Usually trainer_state.json is in the latest checkpoint or root of output_dir
            # We can upload the whole output_dir if needed, but for logs usually lora/logs is enough
            api.upload_folder(
                folder_path="lora/outputs",
                path_in_repo="lora/outputs",
                repo_id=hub_repo_id,
                token=hf_token
            )

    # 8. Export GGUF
    if export_gguf:
        print("Exporting to GGUF (q8_0)...")
        gguf_path = f"lora/qwen2.5-0.5b-q8_0.gguf"
        # unsloth saves as a folder, but we can manage it
        model.save_pretrained_gguf("lora/model_gguf", tokenizer, quantization_method = "q8_0")
        
        if push_to_hub and hub_repo_id:
            print(f"Pushing GGUF to Hub: {hub_repo_id}...")
            model.push_to_hub_gguf(hub_repo_id, tokenizer, quantization_method = "q8_0", token=hf_token)

    # 9. Test Scenarios
    print("\n" + "="*50)
    print("Running Post-Training Test Scenarios")
    print("="*50)
    
    test_questions = []
    test_csv_path = "data/test_questions.csv"
    
    if os.path.exists(test_csv_path):
        import csv
        print(f"Loading test questions from {test_csv_path}...")
        with open(test_csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                test_questions.append({
                    "scenario": row['scenario'], 
                    "difficulty": row.get('difficulty', 'N/A'),
                    "q": row['question']
                })
    else:
        # Fallback if CSV is missing
        print(f"Warning: {test_csv_path} not found. Using minimal fallback.")
        test_questions = [
            {"scenario": 1, "difficulty": "simple", "q": "请解释这段代码的逻辑。"},
            {"scenario": 2, "difficulty": "simple", "q": "请设计一个基础架构。"}
        ]

    FastLanguageModel.for_inference(model)
    
    results = []
    for i, item in enumerate(test_questions):
        print(f"\n[Scenario {item['scenario']} | {item['difficulty']}] Test {i+1}: {item['q']}")
        prompt = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{item['q']}<|im_end|>\n<|im_start|>assistant\n"
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7, top_p=0.9)
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        print(f"Response: {response[:200]}...") # Print snippet
        results.append(f"Q: [{item['difficulty']}] {item['q']}\nA: {response}\n" + "-"*30)

    # Save results to a file
    with open("lora/test_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    
    if push_to_hub and hub_repo_id:
        from huggingface_hub import HfApi
        api = HfApi()
        print("Uploading test results to Hub...")
        api.upload_file(
            path_or_fileobj="lora/test_results.txt",
            path_in_repo="lora/test_results.txt",
            repo_id=hub_repo_id,
            token=hf_token
        )

    print("\nTraining, export and testing finished.")
    return "Training and Testing Success!"

if __name__ == "__main__":
    run_training()
