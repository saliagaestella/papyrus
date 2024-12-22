import openai


models = openai.Model.list()

# Print model names
for model in models.data:
    print(model.id)