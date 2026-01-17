"""
使用已训练的 LoRA 权重对 test_questions_fullLength.jsonl 中的问题进行推理
注意: 此脚本需要 GPU 和 Unsloth
"""
import json
import torch
import os

# 配置
MODEL_ID = "unsloth/Qwen2.5-0.5B-Instruct"
LORA_PATH = "lora/qwen2.5-0.5b-lora"  # 本地 LoRA 权重路径
TEST_FILE = "data/test_questions_fullLength.jsonl"
OUTPUT_FILE = "lora/test_results_fullLength.txt"

def load_model_and_tokenizer():
    """加载基础模型、分词器和 LoRA 权重（使用 Unsloth）"""
    # 检查 GPU
    if not torch.cuda.is_available():
        raise RuntimeError("推理需要 GPU。请在有 GPU 的环境中运行。")
    
    # 使用 Unsloth 加载模型（与训练时一致）
    from unsloth import FastLanguageModel
    
    max_seq_length = 2048
    dtype = None  # Auto detection
    load_in_4bit = True
    
    print(f"使用 Unsloth 加载模型和 LoRA: {LORA_PATH}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=LORA_PATH,
        max_seq_length=max_seq_length,
        dtype=dtype,
        load_in_4bit=load_in_4bit,
    )
    
    # 设置为推理模式
    FastLanguageModel.for_inference(model)
    print("✅ 模型加载完成")
    
    return model, tokenizer

def format_prompt(question: str, scenario: int) -> str:
    """根据场景格式化提示"""
    if scenario == 1:
        instruction = "分析以下代码片段，并从资深开发者的角度回答一个典型的初级开发者提问。请包含详细的推理过程。"
    else:  # scenario == 2
        instruction = "基于提供的代码架构概览，为新需求设计一套技术方案。请包含详细的设计推理过程，并确保方案符合现有架构模式。"
    
    messages = [
        {"role": "system", "content": "你是一位资深的软件工程师，擅长代码分析和架构设计。"},
        {"role": "user", "content": f"{instruction}\n\n{question}"}
    ]
    
    return messages

def run_inference(model, tokenizer, test_data):
    """对所有问题运行推理"""
    results = []
    
    for idx, entry in enumerate(test_data, 1):
        scenario = entry['scenario']
        difficulty = entry['difficulty']
        question_input = entry['input']
        
        print(f"\n{'='*60}")
        print(f"问题 {idx} - Scenario {scenario} - {difficulty}")
        print(f"{'='*60}")
        
        # 格式化提示
        messages = format_prompt(question_input, scenario)
        
        # 使用分词器的 apply_chat_template
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 编码输入
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # 生成回答
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
        
        # 解码输出
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        
        # 保存结果
        result_entry = {
            'question_id': idx,
            'test_id': entry.get('test_id', idx),
            'scenario': scenario,
            'difficulty': difficulty,
            'question': question_input[:300] + '...' if len(question_input) > 300 else question_input,
            'response': response
        }
        results.append(result_entry)
        
        # 打印部分回答
        print(f"\n回答预览: {response[:300]}...\n")
    
    return results

def save_results(results, output_path):
    """保存推理结果到文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("微调模型测试结果 (完整问题版本)\n")
        f.write("=" * 80 + "\n\n")
        
        for result in results:
            f.write(f"问题 {result['question_id']} - Scenario {result['scenario']} - {result['difficulty']}\n")
            f.write("-" * 80 + "\n")
            f.write(f"问题: {result['question']}\n\n")
            f.write(f"模型回答:\n{result['response']}\n")
            f.write("\n" + "=" * 80 + "\n\n")
    
    print(f"\n结果已保存到: {output_path}")

def main():
    # 检查文件是否存在
    if not os.path.exists(TEST_FILE):
        print(f"错误: 找不到测试文件 {TEST_FILE}")
        return
    
    if not os.path.exists(LORA_PATH):
        print(f"错误: 找不到 LoRA 权重目录 {LORA_PATH}")
        print("请先确保训练已完成或从 Hub 下载权重")
        return
    
    # 加载测试问题
    print(f"加载测试问题: {TEST_FILE}")
    test_data = []
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            test_data.append(json.loads(line))
    print(f"共加载 {len(test_data)} 个测试问题\n")
    
    # 加载模型
    model, tokenizer = load_model_and_tokenizer()
    
    # 运行推理
    results = run_inference(model, tokenizer, test_data)
    
    # 保存结果
    save_results(results, OUTPUT_FILE)
    
    print("\n推理完成!")

if __name__ == "__main__":
    main()
