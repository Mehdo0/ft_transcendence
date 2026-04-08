# The Data
For the ai to work properly we need to train it on a [dataset]("https://console.cloud.google.com/storage/browser/quickdraw_dataset/full/numpy_bitmap;tab=objects?pli=1&prefix=&forceOnObjectsSortingFiltering=false") . we will use the google quick draw dataset because it fits perfectly the project and provide numpy bitmap files that are already processed by google .
# The Training 
Because we don't have the google process power , we won't be able to use the full 50 million drawings provided by them ... Although we will use 10 distinct categories out of the 345 available . 

After selecting these categories we're going to merge them together into one big file . Then we'll use PyTorch as the machine learning framework .

To check that the ai is correctly training on the dataset and not only perfecting these exact drawings... We'll apply the 80/20 rule:

- **The Training Set (80%)**: The AI will look at these drawings and their labels to learn.

- **The Validation Set (20%)**: You hide these from the AI during learning.

The validation set will be used to check if the AI is able or not to recognize certain patterns and finally guess the drawing ! 