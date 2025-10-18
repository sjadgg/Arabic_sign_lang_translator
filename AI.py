import tensorflow as tf 
import numpy as np

#that is the data which the mode training on (line 13 and 14)
# x is input data and y is the output , first model try to guse the x wich give the same
# result in y , depinding on the result (100% false in the first try) model desided to decrees or increes x
# model trying 500 times each time chinging x value with a new value that get it closer to result y
#to finly get close enugh (aroud 0.0xxx) that point we can say the model got the equation between x and y
#y=x*3+2
 

# x (input) and y (output)   
x= np.array([1,2,3,4,5,6,7,8,9],dtype=float)
y= np.array([5,8,11,14,17,20,23,26,29],dtype=float)

#layers and uints(neruns , nodes)
model = tf.keras.Sequential([
    tf.keras.layers.Dense(units=10, input_shape=[1]),
    tf.keras.layers.Dense(units=5), 
    tf.keras.layers.Dense(units=1) 
])

# chose optimizer(who is adjust a models weights to minimize the error loss)
#and loss (error rate , closer to 0 mean less errors)
model.compile(optimizer='adam', loss='mean_squared_error')

#start training
model.fit(x, y, epochs=500)

#test the result
for x in range(5):
    inp = int(input("inter nmber : "))
    print("ai : ",model.predict(np.array([[inp]])))
    x+1

#save the model if result are good
save = input("save the model ? (y,n) : ")
if save == "y" or "Y" or "yes":
    model.save('my_model.keras')

#if you wana load model any where else just type the code:
# model = tf.keras.models.load_model('my_model.keras')