import re

file = str('D:\Downloads\Test-master\src\1\ziot_r_test.prog.xml')
filename = re.split(r'((?i)ZIOT_\w+)\.\w+', file)
print(filename)