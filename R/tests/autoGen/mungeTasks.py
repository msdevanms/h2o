##
# Munge Task writers: Slicing, Simple Filter, Compound Filter
##

from GenUtils import *
import itertools

def writeSimpleSliceTestTask(FU, data, dataPath, FUParams):
    TESTNAME, DESCRIPTION, COLS, ROWS, COLROW, LOOPCOLS, LOOPROWS, LOOPCOLROW = FUParams.split(':')
    DATANAME = data
    DATAPATH = dataPath
    #{0} is DATANAME
    #{1} is FU
    #{2} is DATAPATH
    #{3} is TESTNAME
    test = """
            source('./Utils/h2oR.R')

            Log.info("======================== Begin Test ===========================")
            {3} <- function(conn) {{
                Log.info("A munge-task R unit test on data <{0}> testing the functional unit <{1}> ")
                Log.info("Uploading {0}")
                hex <- h2o.uploadFile(conn, {2}, "{0}.hex")
           """.format(DATANAME, FU, DATAPATH, TESTNAME)

    cols = makeVec(COLS)
    rows = makeVec(ROWS)
    cR = COLROW.split('|')
    #[rows, cols]
    colRow = [makeVec(cR[1]), makeVec(cR[0])]
    loopCols = convertSeq(filter(lambda a: a in ['0', 0],LOOPCOLS.split(';')))
    loopRows = convertSeq(filter(lambda a: a in ['0', 0], LOOPROWS.split(';')))
    loopColRow = LOOPCOLROW.split('|')
    
    #[(row,col),(row,col),...]
    loopColsRows = list(itertools.product(*[loopColRow[1].split(';'), loopColRow[0].split(';')])) 

    #{0} is cols
    colSlice = """
                slicedHex <- hex[,{0}]
               """
    #{0} is rows
    rowSlice = """
                slicedHex <- hex[{0},]
               """

    colRowSlice = \
               """
                slicedHex <- hex[{0},{1}]
               """
    if cols != '0' and cols != 'c()':
        #{0} is DATANAME
        #{1} is cols to slice by
            test += """
                
                Log.info("Performing a column slice of {0} using these columns: {1}")""".format(DATANAME, escape(cols))
            test += colSlice.format(cols)

    if rows not in ['0',0, '',"","c()", "c(0)"]:
        #{0} is DATANAME
        #{1} is rows to slice by
            
            test += """
                
                    Log.info("Performing a row slice of {0} using these rows: {1}")
                """.format(DATANAME, rows)
            test += rowSlice.format(rows)

    if colRow[0] not in ["c(0)","c()",'c("")',"",'','0',0, 'c("")'] and colRow[1] not in ["c(0)","c()",'c("")',"",'','0',0, 'c("")']:
        #{0} is DATANAME
        #{1} is rows to slice by
        #{2} is cols to slice by
        test += """
                
                    Log.info("Performing a row & column slice of {0} using these rows & columns: {2} & {1}")
                """.format(DATANAME, colRow[0], escape(colRow[1]))
        test += colRowSlice.format(colRow[0], colRow[1])
        
    if not any(x in loopCols for x in ['"0"',"0",'0', 0, '', "", "c()", "c(0)"]): 
        #{0} is DATANAME
        #{1} is loopCols to slice by
        test += """ 
                
                    Log.info("Performing a 1-by-1 column slice of {0} using these columns: {1}")
                """.format(DATANAME, escape(','.join(loopCols)))
        for i in loopCols:
            test += \
                """
                    Log.info("Slicing column {1} from data {0}")
                """.format(DATANAME, escape(i))
            test += colSlice.format(i)

    if not any(x in loopRows for x in ["c(0)","c()",'c("")',"",'','0',0, 'c("")']):
        #{0} is DATANAME
        #{1} is loopRows to slice by
        test += """ 
                
                    Log.info("Performing a 1-by-1 row slice of {0} using these rows: {1}")
                """.format(DATANAME, ','.join(loopRows))
        for i in loopRows:
            test += \
                """
                    Log.info("Slicing row {1} from data {0}")
                """.format(DATANAME, i)
            test += rowSlice.format(i)

    if not any(x in loopColRow[0] for x in ['"0"',"0",'0', '', "", "c()", "c(0)", 'c("")']) or not any(x in loopColRow[1] for x in ['"0"',"0",'0', '', "", "c()", "c(0)", 'c("")']):   
        #{0} is DATANAME
        #{1} is rows to loop over
        #{2} is cols to loop over
        test += """ 
                
                    Log.info("Performing a 1-by-1 combined row & column slice of {0} using these rows & columns: {1} & {2}")
                """.format(DATANAME, escape(','.join(loopColRow[1].split(';'))), escape(','.join(loopColRow[0].split(';'))))
        for i in loopColsRows:
            test += \
                """
                    Log.info("Slicing row {1} and column {2} from data {0}")
                """.format(DATANAME, escape(i[0]), escape(i[1]))
            test += colRowSlice.format(i[0], i[1])

    test += """
            }}
            
            conn = new("H2OClient", ip=myIP, port=myPort)
            tryCatch(test_that({1}, {0}(conn)), error = function(e) FAIL(e))
            PASS()""".format(TESTNAME, DESCRIPTION)

    return test

def writeSimpleNumericFilterTestTask(FU, data, dataPath, FUParams):
    TESTNAME, DESCRIPTION, COLS, VALUECOL, VALUECOL2 = FUParams.split(':')
    DATANAME = data
    DATAPATH = dataPath
    #{0} is DATANAME
    #{1} is FU
    #{2} is DATAPATH
    #{3} is TESTNAME
    test = """ 
            source('./Utils/h2oR.R')

            Log.info("======================== Begin Test ===========================")
            {3} <- function(conn) {{
                Log.info("A munge-task R unit test on data <{0}> testing the functional unit <{1}> ")
                Log.info("Uploading {0}")
                hex <- h2o.uploadFile(conn, {2}, "{0}.hex")
           """.format(DATANAME, FU, DATAPATH, TESTNAME)

    valCol = zip(VALUECOL.split('|')[0].split(';'), VALUECOL.split('|')[1].split(';'))
    valCol2 = zip(VALUECOL2.split('|')[0].split(';'), VALUECOL2.split('|')[1].split(';')) if VALUECOL2 != '0' else '0'
    compCols = COLS.split(';') 
    #{0} is FU
    #{1} is column index or name (valCol[i][1])
    #{2} is value (valCol[i][0])
    rowFilterByCol = """
                     filterHex <- hex[hex[,{1}] {0} {2},]
                     """
    rowFilterByColNSelect = \
                     """
                     filterHex <- hex[hex[,{1}] {0} {2}, {3}]
                     """
    rowFilterByMunee = ""
    rowFilterByMuneeNSelect = ""
    try:
        float(valCol[0][1])
    except ValueError:
        rowFilterByMunee = \
                    """
                    filterHex <- hex[hex${1} {0} {2},]
                    """
        rowFilterByMuneeNSelect = \
                    """
                    filterHex <- hex[hex${1} {0} {2}, {3}]
                    """

    for i in valCol:
        #{0} is FU
        #{1} is DATANAME
        #{2} is i[1] (valCol[j][1])
        #{3} is i[0] (valCol[j][0])
        if i[0] in ['0', 0, '', ""]: continue
        if i[1] in ['0', 0, '', ""]: continue
        test += """
                Log.info("Filtering out rows by {0} from dataset {1} and column {2} using value {3}")
                """.format(FU, DATANAME, escape(i[1]), escape(i[0]))

        test += rowFilterByCol.format(FU, makeVec(i[1]), i[0])
        if rowFilterByMunee != "":
            test += """
                    Log.info("Perform filtering with the '$' sign also")
                    """
            test += rowFilterByMunee.format(FU, i[1], i[0])

    if valCol2 != '0':
        for i in valCol2:
            #{0} is FU
            #{1} is DATANAME
            #{2} is i[1] (valCol[j][1])
            #{3} is i[0] (valCol[j][0])
            if i[0] in ['0', 0, '', ""]: continue
            if i[1] in ['0', 0, '', ""]: continue
            test += """ 
                    Log.info("Filtering out rows by {0} from dataset {1} and column {2} using value {3}, and also subsetting columns.")
                    """.format(FU, DATANAME, escape(i[1]), escape(i[0]))

            test += rowFilterByColNSelect.format(FU, makeVec(i[1]), i[0], makeVec(i[1]))
            test += """
                    Log.info("Now do the same filter & subset, but select complement of columns.")
                    """
            cC = filter(lambda a: a != i[1], compCols)
            test += rowFilterByColNSelect.format(FU, makeVec(i[1]), i[0], makeVec(';'.join(cC)))
    test += """ 
            }}
            
            conn = new("H2OClient", ip=myIP, port=myPort)
            tryCatch(test_that({1}, {0}(conn)), error = function(e) FAIL(e))
            PASS()""".format(TESTNAME, DESCRIPTION)

    return test

def writeCompoundFilterTestTask(FU, data, dataPath, FUParams):
    FU = FU.split(';')
    TESTNAME, DESCRIPTION, COLS, VALUECOLL, VALUECOLR, VALUECOLL2, VALUECOLR2 = FUParams.split(':')
    DATANAME = data
    DATAPATH = dataPath
    #{0} is DATANAME
    #{1} is FU
    #{2} is DATAPATH
    #{3} is TESTNAME
    test = """ 
            source('./Utils/h2oR.R')

            Log.info("======================== Begin Test ===========================")
            {3} <- function(conn) {{
                Log.info("A munge-task R unit test on data <{0}> testing the compound functional unit <{1}> ")
                Log.info("Uploading {0}")
                hex <- h2o.uploadFile(conn, {2}, "{0}.hex")
           """.format(DATANAME, FU, DATAPATH, TESTNAME)

    valColL = zip(VALUECOLL.split('|')[0].split(';'), VALUECOLL.split('|')[1].split(';'))
    valColR = zip(VALUECOLR.split('|')[0].split(';'), VALUECOLR.split('|')[1].split(';'))
    valCol  = zip(valColL, valColR)

    valColL2 = zip(VALUECOLL2.split('|')[0].split(';'), VALUECOLL2.split('|')[1].split(';')) if VALUECOLL2 != '0' else '0'
    valColR2 = zip(VALUECOLR2.split('|')[0].split(';'), VALUECOLR2.split('|')[1].split(';')) if VALUECOLR2 != '0' else '0'
    valCol2  = zip(valColL2, valColR2)

    compCols = COLS.split(';')
    #{0} is the compound expression
    #{1} is the column selection
    rowFilterByCol = """
                     filterHex <- hex[{0},]
                     """
    rowFilterByColNSelect = \
                     """
                     filterHex <- hex[{0}, {1}]
                     """

    #TODO: Implement the $ select as well
    #rowFilterByMunee = ""
    #rowFilterByMuneeNSelect = ""
    #try:
    #    float(valCol[0][1])
    #except ValueError:
    #    rowFilterByMunee = \
    #                """
    #                filterHex <- hex[hex${1} {0} {2},]
    #                """
    #    rowFilterByMuneeNSelect = \
    #                """
    #                filterHex <- hex[hex${1} {0} {2}, {3}]
    #                """

    FUcopy = FU[:]
    EXPRESSION = makeExpression(FUcopy, valCol)
        
    test += """ 
            Log.info("Performing compound task {0} on dataset <{1}>")
            """.format(escape(EXPRESSION), DATANAME)

    test += rowFilterByCol.format(EXPRESSION)

    if valCol2[0][0][0] != "'0'":
        FUcopy = FU[:]
        EXPRESSION = makeExpression(FUcopy, valCol2)
        test += \
            """ 
            Log.info("Performing compound task {0} on dataset {1}, and also subsetting columns.")
            """.format(escape(EXPRESSION), DATANAME)

        selectCols = [i[1].replace('"','') for i in valColL2] + [i[1] for i in valColR2]
        selectCols = [i.replace('"','') for i in selectCols]
        test += rowFilterByColNSelect.format(EXPRESSION, makeVec(';'.join(selectCols)))
        test += """
                Log.info("Now do the same filter & subset, but select complement of columns.")
                """
        cC = filter(lambda a: a not in selectCols, compCols)
        test += rowFilterByColNSelect.format(EXPRESSION, makeVec(';'.join(cC)))

    test += """
            }}
            
            conn = new("H2OClient", ip=myIP, port=myPort)
            tryCatch(test_that({1}, {0}(conn)), error = function(e) FAIL(e))
            PASS()""".format(TESTNAME, DESCRIPTION)

    return test
