from openai import OpenAI
import httpx
import os

client = OpenAI(
    base_url="https://api.chatanywhere.tech/v1",
    api_key="sk-39X6rU2Auzqqtzxj0BCxV2b7lZeeILmreNBcAv7VUwHVd88A"
)


def get_gpt_response( user_input):
    # 初始请求
    completion = client.chat.completions.create(
        model=model_version,
        messages=[
            {"role": "user", "content": user_input}
        ],
    )

    # 打印初始AI回答
    initial_response = completion.choices[0].message.content
    print(initial_response)
    return initial_response

# 流式调用
def gpt_35_api_stream(messages: list):
    """为提供的对话消息创建新的回答 (流式传输)

    Args:
        messages (list): 完整的对话消息
    """
    stream = client.chat.completions.create(
        model=model_version,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")


def concatenate_sentences(directory):
    concatenated_sentence = ""

    # Get all file names in the directory and sort them numerically
    file_names = sorted([f for f in os.listdir(directory) if f.endswith('.txt')], key=lambda x: int(x.split('.')[0]))

    # Loop through each sorted file
    for filename in file_names:
        filepath = os.path.join(directory, filename)

        # Read the file and add its contents to the concatenated sentence
        if os.path.isfile(filepath):
            with open(filepath, 'r') as file:
                sentence = file.read().strip()
                concatenated_sentence += sentence + " "  # Add a space between sentences

    return concatenated_sentence

projects = ['teammates', 'bigbluebutton', 'jabref', 'mediastore', 'teastore']
number_of_iterations = 10  # Change this number as needed
model_version='gpt-4o'
for project in projects:
    folder_name = 'LLM_responses/'+model_version+'/'+project
    # Directory containing the sentences
    directory_path = 'data/ftlr-texts/'+project

    # 读取架构文档Concatenate sentences from all files
    user_input = concatenate_sentences(directory_path)
    user_input = "Here is a description of a software architecture document: ["+user_input+"]. Please extract all the architecture modules with their types and descriptions. And be sure not to repeat, cluster together modules with similar functional representations. Ensure that modules with similar functional representations are clustered together, and avoid repetitions. You must pay attention to the output format. The format of the output example is as follows: module name: , module description: .(Make sure the output form begins with module name: or module description:). In addition, keep the module name to one word in length."
    initial_prompt = "You are a skilled software architect. Your task is to analyze architecture documents and extract module names and descriptions from them.  Please try to give high-level abstract modules. "

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    # Get the current count of output files
    existing_files = [f for f in os.listdir(folder_name) if f.startswith('output_') and f.endswith('.txt')]
    existing_count = len(existing_files)

    # Calculate the starting index for new files
    start_index = existing_count + 1

    for i in range(start_index, start_index + number_of_iterations):
        # Simulate getting a response from GPT
        response = get_gpt_response(user_input)  # Assuming get_gpt_response is defined elsewhere

        # Write the response to a file
        with open(os.path.join(folder_name, f'output_{i}.txt'), 'w') as file:
            file.write(response)


