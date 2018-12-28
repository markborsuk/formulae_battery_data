import pandas as pd
import re

def convert_dataframe_to_lines(dataframe, measurement, field_columns=[],
                                tag_columns=[], global_tags={},
                                time_precision=None, numeric_precision=None):

    # if not isinstance(dataframe, pd.DataFrame):
    #     raise TypeError('Must be DataFrame, but type was: {0}.'
    #                     .format(type(dataframe)))
    # if not (isinstance(dataframe.index, pd.tseries.period.PeriodIndex) or
    #         isinstance(dataframe.index, pd.tseries.index.DatetimeIndex)):
    #     raise TypeError('Must be DataFrame with DatetimeIndex or \
    #                     PeriodIndex.')

    string_columns = dataframe.select_dtypes(include=['object']).columns

    if field_columns is None:
        field_columns = []
    if tag_columns is None:
        tag_columns = []

    field_columns = list(field_columns) if list(field_columns) else []
    tag_columns = list(tag_columns) if list(tag_columns) else []

    # Assume that all columns not listed as tag columns are field columns
    if not field_columns:
        field_columns = list(set(dataframe.columns).difference(set(tag_columns)))

    precision_factor = {
        "n": 1,
        "u": 1e3,
        "ms": 1e6,
        "s": 1e9,
        "m": 1e9 * 60,
        "h": 1e9 * 3600,
    }.get(time_precision, 1)


    # Make array of timestamp ints
    time = ((dataframe.index.astype(int) / precision_factor)
            .astype(int).astype(str))

    # If tag columns exist, make an array of formatted tag keys and values
    if tag_columns:
        tag_df = dataframe[tag_columns]
        tag_df = _stringify_dataframe(tag_df, numeric_precision)
        tags = (',' + ((tag_df.columns + '=').tolist() + tag_df)).sum(axis=1)
        del tag_df

    else:
        tags = ''

    # Make an array of formatted field keys and values
    field_df = dataframe[field_columns]
    field_df = _stringify_dataframe(field_df, numeric_precision)
    field_df[string_columns] = '"' + field_df[string_columns] + '"'
    field_df = (field_df.columns + '=').tolist() + field_df
    field_df[field_df.columns[1:]] = ',' + field_df[field_df.columns[1:]]
    fields = field_df.sum(axis=1)
    del field_df

    # Add any global tags to formatted tag strings
    if global_tags:
        global_tags = ','.join(['='.join([tag, global_tags[tag]])
                            for tag in global_tags])
        if tag_columns:
            tags = tags + ',' + global_tags
        else:
            tags = ',' + global_tags

    # Generate line protocol string
    points = (measurement +  tags + ' ' +
            fields + ' ' + time).tolist()
    return points

def _stringify_dataframe(dataframe, numeric_precision):
    float_columns = dataframe.select_dtypes(include=['floating']).columns
    nonfloat_columns = dataframe.columns[
        ~dataframe.columns.isin(float_columns)
    ]
    numeric_columns = dataframe.select_dtypes(include=['number']).columns

    # Convert dataframe to string
    if numeric_precision is None:
        dataframe = dataframe.astype(str)
    elif numeric_precision == 'full':
        dataframe[float_columns] = dataframe[float_columns].applymap(repr)
        dataframe[nonfloat_columns] = dataframe[nonfloat_columns].astype(str)
    elif isinstance(numeric_precision, int):
        dataframe[numeric_columns] = (dataframe[numeric_columns]
                                    .round(numeric_precision))
        dataframe = dataframe.astype(str)
    else:
        raise ValueError('Invalid numeric precision')
    dataframe.columns = dataframe.columns.astype(str)
    return dataframe


def csv_to_line(file_name):
    #convert csv's to line protocol

    #convert sample data to line protocol (with nanosecond precision)
    df = pd.read_csv("data/" + file_name)
    lines = ["RESSData"
             + ",type=AUD"
             + " "
             + "IBatt=" + str(df["BMU_Stats_Pack_Curr"][d]) + ","
             + "VBatt=" + str(df["BMU_Stats_Pack_Vbatt"][d]) + ","
             + "TCellMax=" + str(df["BMU_Stats_Temp_Cell_Max"][d]) + ","
             + "rSOC=" + str(df["BMU_Stats_Pack_Soc"][d])
             + " " + str(df["SecondsIntoDay"][d]) for d in range(len(df))]
    file_name = re.sub('\.csv','.txt', file_name)
    thefile = open('data/'+ file_name, 'w')
    for item in lines:
        thefile.write("%s\n" % item)

def nano_precision(file_name):

    # Convert from second precision to nanosecond precision.

    df = pd.read_csv('data/' + file_name)
    df.head()
    # convert minute precision to nanosecond precision
    df["SecondsIntoDay"] = [str(int(df["SecondsIntoDay"][t]*1e9)) for t in range(len(df))]
    df.head()
    # export as csv
    ns_precision = df
    file_name = re.sub("\.csv", '_ns.csv', file_name)
    ns_precision.to_csv('data/' + file_name, index=False)

    return file_name