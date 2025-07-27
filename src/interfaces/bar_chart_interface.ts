export default interface BarChartInterface {
  labels: Array<string>,
  datasets: Array<barChartDatasetType>
}

type barChartDatasetType = {
  label: string,
  data: Array<number>,
  backgroundColor: Array<string> | string,
  borderColor?: Array<string> | string,
  borderWidth?: number
}