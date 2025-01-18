import simpleRestProvider from 'ra-data-simple-rest';

// Customize the base URL of your API
const dataProvider = (apiUrl) => simpleRestProvider(apiUrl);

export default dataProvider;
