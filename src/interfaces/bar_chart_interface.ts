export default interface BarChartInterface {
  labels: Array<string>,
  datasets: Array<barChartDatasetType>
}

type barChartDatasetType = {
  label: string,
  data: Array<number>,
  backgroundColor: Array<string> | string,
  color?: string,
  borderColor?: Array<string> | string,
  borderWidth?: number
}