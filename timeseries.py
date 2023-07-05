import pyspark.sql.functions  as f
from pyspark.sql.window import Window
from pyspark.sql import SparkSession

streaming_data = [("U1", "2019-01-01T11:00:00Z"),
                  ("U1", "2019-01-01T11:15:00Z"),
                  ("U1", "2019-01-01T12:00:00Z"),
                  ("U1", "2019-01-01T12:20:00Z"),
                  ("U1", "2019-01-01T15:00:00Z"),
                  ("U2", "2019-01-01T11:00:00Z"),
                  ("U2", "2019-01-02T11:00:00Z"),
                  ("U2", "2019-01-02T11:25:00Z"),
                  ("U2", "2019-01-02T11:50:00Z"),
                  ("U2", "2019-01-02T12:15:00Z"),
                  ("U2", "2019-01-02T12:40:00Z"),
                  ("U2", "2019-01-02T13:05:00Z"),
                  ("U2", "2019-01-02T13:20:00Z")]
schema = ("UserId", "Click_Time")
window_spec = Window.partitionBy("UserId").orderBy("Click_Time")

spark =  SparkSession.builder.master("local").appName("upesh").getOrCreate()
df_stream = spark.createDataFrame(streaming_data, schema)
df_stream = df_stream.withColumn("Click_Time", df_stream["Click_Time"].cast("timestamp"))

df_stream = df_stream \
    .withColumn("time_diff",
                (f.unix_timestamp("Click_Time") - f.unix_timestamp(f.lag(f.col("Click_Time"), 1).over(window_spec))) / (
                            60 * 60)).na.fill(0)

df_stream = df_stream \
    .withColumn("cond_", f.when(f.col("time_diff") > 1, 1).otherwise(0))
df_stream = df_stream.withColumn("temp_session", f.sum(f.col("cond_")).over(window_spec))
new_window = Window.partitionBy("UserId", "temp_session").orderBy("Click_Time")
new_spec = new_window.rowsBetween(Window.unboundedPreceding, Window.currentRow)
cond_2hr = (f.unix_timestamp("Click_Time") - f.unix_timestamp(f.lag(f.col("Click_Time"), 1).over(new_window)))
df_stream = df_stream.withColumn("temp_session_2hr",
                                 f.when(f.sum(f.col("2hr_time_diff")).over(new_spec) - (2 * 60 * 60) > 0, 1).otherwise(
                                     0))
new_window_2hr = Window.partitionBy(["UserId", "temp_session", "temp_session_2hr"]).orderBy("Click_Time")
hrs_cond_ = (f.when(
    f.unix_timestamp(f.col("Click_Time")) - f.unix_timestamp(f.first(f.col("Click_Time")).over(new_window_2hr)) - (
                2 * 60 * 60) > 0, 1).otherwise(0))
df_stream = df_stream \
    .withColumn("final_session_groups", hrs_cond_)

df_stream = df_stream.withColumn("final_session", df_stream["temp_session_2hr"] + df_stream["temp_session"] + df_stream[
    "final_session_groups"] + 1) \
    .drop("temp_session", "final_session_groups", "time_diff", "temp_session_2hr", "final_session_groups")
df_stream = df_stream.withColumn("session_id",
                                 f.concat(f.col("UserId"), f.lit(" session_val----->"), f.col("final_session")))
df_stream.show(20, 0)