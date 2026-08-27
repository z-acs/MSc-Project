import pandas as pd

df = pd.read_csv("hotel_bookings.csv")

df.head(1000).to_csv("hotel_bookings_1000.csv", index=False)
df.head(10000).to_csv("hotel_bookings_10000.csv", index=False)
df.head(50000).to_csv("hotel_bookings_50000.csv", index=False)

print("Done!")