import React, { useEffect, useState } from 'react';
import BootstrapTable from 'react-bootstrap-table-next';
import cellEditFactory from 'react-bootstrap-table2-editor';
import axios from 'axios';
import Plot from 'react-plotly.js';

function App() {
  const [avgSV, setAvgSV] = useState({});
  const [tableData, setTableData] = useState([]);
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5001/data')
      .then(response => {
        setAvgSV(response.data.avg_sv);
        const processedData = processTableData(response.data.data);
        setTableData(processedData);
        const columns = Object.keys(processedData[0] || {}).map(key => ({
          dataField: key,
          text: key,
          sort: true,
        }));
        setColumns(columns);
      })
      .catch(error => console.error(`There was an error retrieving the data: ${error}`));
  }, []);

  const processTableData = (data) => {
    let tableData = {};
    for (let period in data) {
      for (let keyword in data[period]) {
        if (!tableData[keyword]) {
          tableData[keyword] = { Keyword: keyword };
        }
        tableData[keyword][period] = data[period][keyword];
      }
    }
    return Object.values(tableData);
  };

  return (
    <div className="App">
      <Plot
        data={[
          {
            type: 'scatter',
            mode: 'lines',
            x: Object.keys(avgSV),
            y: Object.values(avgSV),
            marker: { color: 'red' },
          }
        ]}
        layout={{ autosize: true, title: 'A Fancy Plot' }}
      />

      {columns.length > 0 && (
        <BootstrapTable
          keyField='Keyword'
          data={ tableData }
          columns={ columns }
          cellEdit={ cellEditFactory({ mode: 'click', blurToSave: true }) }
        />
      )}
    </div>
  );
}

export default App;

