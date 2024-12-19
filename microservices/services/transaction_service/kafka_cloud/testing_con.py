class Test:
    def __str__(self):
        print('hello')
    
    def __eq__(self, value):
        print('hello')

print(Test.__str__)