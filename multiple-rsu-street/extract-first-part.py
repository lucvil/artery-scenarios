# extract 5000 lines from General-#0.elog
with open('./results/filtered-General-#0.elog', 'r') as file:
    lines = file.readlines()

extracted_lines = lines[:30000]

# write log.txt
with open('./results/log.txt', 'w') as file:
    file.writelines(extracted_lines)
