import streamlit as st
import pandas as pd
import time

# Leaky Bucket Class
class LeakyBucket:
    def __init__(self, capacity, leak_rate):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.current_packets = 0
        self.total_dropped = 0

    def add_packets(self, packets_to_add):
        space_remaining = self.capacity - self.current_packets
        if packets_to_add <= space_remaining:
            self.current_packets += packets_to_add
            return 0
        else:
            self.current_packets = self.capacity
            dropped = packets_to_add - space_remaining
            self.total_dropped += dropped
            return dropped

    def leak_packets(self):
        if self.current_packets > 0:
            packets_leaked = min(self.current_packets, self.leak_rate)
            self.current_packets -= packets_leaked
            return packets_leaked
        return 0

# Token Bucket Class with Continuous Token Addition
class TokenBucket:
    def __init__(self, capacity, token_rate):
        self.capacity = capacity  # Max tokens the bucket can hold
        self.token_rate = token_rate  # Tokens added per second
        self.tokens = 0  # Current number of tokens in the bucket
        self.last_updated = time.time()  # Track the last time tokens were updated
        self.total_dropped = 0  # Total dropped packets due to lack of tokens

    def add_packets(self, packets_to_add):
        # Add tokens based on the elapsed time since the last update
        current_time = time.time()
        elapsed_time = current_time - self.last_updated
        self.tokens += elapsed_time * self.token_rate
        self.tokens = min(self.tokens, self.capacity)  # Cap tokens at the capacity
        self.last_updated = current_time  # Update the last time token update happened
        
        # Check if there are enough tokens for the incoming packets
        if packets_to_add <= self.tokens:
            self.tokens -= packets_to_add  # Consume tokens
            return 0  # No packets dropped
        else:
            dropped = packets_to_add - self.tokens
            self.tokens = 0  # All tokens are used up
            self.total_dropped += dropped  # Increment dropped packets count
            return dropped  # Return the number of dropped packets

# Streamlit app to visualize the simulation
def run_streamlit_app():
    st.title("Bucket Simulation")
    st.sidebar.subheader("Simulation Parameters")
    bucket_type = st.sidebar.radio("Choose Bucket Type", ["Leaky Bucket", "Token Bucket"])
    capacity = st.sidebar.number_input("Bucket Capacity", min_value=1, max_value=100, value=20)
    
    if bucket_type == "Leaky Bucket":
        leak_rate = st.sidebar.number_input("Leak Rate (packets/sec)", min_value=1, max_value=50, value=5)
        bucket = LeakyBucket(capacity=capacity, leak_rate=leak_rate)
    else:
        token_rate = st.sidebar.number_input("Token Rate (tokens/sec)", min_value=1, max_value=50, value=5)
        bucket = TokenBucket(capacity=capacity, token_rate=token_rate)

    incoming_rate = st.sidebar.number_input("Incoming Packet Rate (packets/sec)", min_value=1, max_value=50, value=10)
    total_packets = st.sidebar.number_input("Total Number of Packets", min_value=1, max_value=500, value=100)

    logs = []
    bucket_state = []
    dropped_packets = []
    leaked_packets = []

    for second in range(total_packets // incoming_rate + 1):
        packets_to_add = incoming_rate
        if bucket_type == "Leaky Bucket":
            dropped = bucket.add_packets(packets_to_add)
            leaked = bucket.leak_packets()
        else:
            dropped = bucket.add_packets(packets_to_add)
            leaked = 0

        log_entry = {
            "Second": second + 1,
            "Packets Added": packets_to_add,
            "Dropped Packets": dropped,
            "Current Bucket State": bucket.current_packets if bucket_type == "Leaky Bucket" else bucket.tokens,
            "Total Dropped": bucket.total_dropped
        }
        
        if bucket_type == "Leaky Bucket":
            log_entry["Leaked Packets"] = leaked

        logs.append(log_entry)
        bucket_state.append(bucket.current_packets if bucket_type == "Leaky Bucket" else bucket.tokens)
        dropped_packets.append(dropped)
        if bucket_type == "Leaky Bucket":
            leaked_packets.append(leaked)

        time.sleep(0.5)

    logs_df = pd.DataFrame(logs)
    st.write("### Simulation Log")
    st.dataframe(logs_df)
    st.write("### Simulation Graphs")

    st.markdown("#### Bucket State (Current Tokens or Packets) Over Time")
    bucket_state_df = pd.DataFrame(bucket_state, columns=["Bucket State"])
    st.line_chart(bucket_state_df, use_container_width=True)

    st.markdown("#### Dropped Packets Over Time")
    dropped_packets_df = pd.DataFrame(dropped_packets, columns=["Dropped Packets"])
    st.line_chart(dropped_packets_df, use_container_width=True)

    if bucket_type == "Leaky Bucket":
        st.markdown("#### Leaked Packets Over Time (Leaky Bucket Only)")
        leaked_packets_df = pd.DataFrame(leaked_packets, columns=["Leaked Packets"])
        st.line_chart(leaked_packets_df, use_container_width=True)

    st.write("### Summary")
    st.write(f"Total Packets Added: {total_packets}")
    st.write(f"Total Packets Dropped: {bucket.total_dropped}")
    st.write(f"Final Bucket State: {bucket.current_packets if bucket_type == 'Leaky Bucket' else bucket.tokens}")

if __name__ == "__main__":
    run_streamlit_app()
