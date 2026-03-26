def get_stages():
    res = []
    with open("ci/ci.txt") as f:
        for line in f:
            line = line.strip()
            if line.startswith("stages:"):
                continue
            if not line.startswith("-"):
                break

            res.append(line[2:])

    if res != []:
        return res
    return False

def get_jobs_from_stages(*args):
    res = []
    all_lines = []
    temp = ''
    with open("ci/ci.txt", "r", encoding="UTF-8") as f:
        for line in f:
            all_lines.append(line)

        for i in range(len(all_lines)):
            if not all_lines[i].startswith(" "):
                temp = all_lines[i].strip()

            if "stage:\n" in all_lines[i] and all_lines[i + 1].strip() in args[0]:
                res.append(temp[0:-1])
            if "stage: " in all_lines[i] and all_lines[i].strip().split(" ")[-1] in args[0]:
                res.append(temp[0:-1])

    return all_lines, res

# def create_pipeline_jobs(lines, jobs):
#     content = ''
#     flag = False
#
#     for i in range(len(lines)):
#         if not lines[i].startswith(" ") and flag == True :
#             flag = False
#
#         if flag:
#             content += lines[i]
#
#         if lines[i].rstrip()[:-1] in jobs and flag == False :
#             flag = True
#             content += lines[i]
#
#     return content
#
# def create_pipeline_stages(stages):
#     content = 'stages:\n\t'
#
#     for stage in stages:
#         content += f"- {stage}\n\t"
#     content += '\n\n'
#
#     return content
#
# def test_pipe(content_stage, content_jobs):
#     content = content_stage + content_jobs
#
#     try:
#         with open("ci/.gitlab-ci.yml", "w", encoding="UTF-8") as f:
#             f.write(content)
#     except Exception as e:
#         print(e)
#         return False
#     return True
#
# test_pipe(create_pipeline_stages(['compile', 'build']), create_pipeline_jobs(*get_jobs_from_stages(['build', 'compile'])))