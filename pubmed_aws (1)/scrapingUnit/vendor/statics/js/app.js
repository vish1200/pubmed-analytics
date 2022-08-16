var suggestion_url = "/suggestions?term=";
var excel_file = "";
var results = [];
var table = null;

// vars for jobs
var job_id = null;
var job_type = null;
var job_end = Date.now() / 1000 + 300;
var pdf_downloaded = false;
var text_extracted = false;
var hostName = `https://${window.location.hostname}`;


function check_url() {
    let url = window.location.href;
    if (url.charAt(url.length - 1) === '/') {
        window.location.href = url.substring(0, url.length - 1);
    }
}


// Async Ajax Request
function AjaxRequest(url, method='GET', data=null, alertable=true){
    return new Promise((resolve, reject) => {
       $.ajax({
            url : url,
            method : method,
            contentType: "application/json",
            data : data,
            success :  function(res){
                resolve(res);
            },
            error: function(err){
                if (alertable){
                    alert("Error was occurred!");
                    hide_spinner();
                }
                reject(false);
            }
       });
    });
}


// show Spinner
function show_spinner(){
    $('#spinner').css('display', 'block');
}


// hide Spinner
function hide_spinner(){
    $('#spinner').css('display', 'none');
}


function setDownloadableState(type="") {
    $('.results-div, #export_excel_button, #export_pdf_button, #export_txt_button').css('display', 'none');
    if (type === "excel") {
        $('.results-div, #export_excel_button').css('display', '');
    } else if (type === "pdf") {
        $('.results-div, #export_excel_button, #export_pdf_button').css('display', '');
    } else if (type === "text") {
        $('.results-div, #export_excel_button, #export_pdf_button, #export_txt_button').css('display', '');
    }
    hide_spinner();
}


async function check_downloadable(urlToSend) {
    return await AjaxRequest(urlToSend, "HEAD", null, alertable=false);
}


function downloadFilePromise(fileUrl) {
    /**
     *  File downloading using fetch,
     *  Show save modal and file saving to selected destination
     * */
    return new Promise( (resolve, reject) => {
        fetch(fileUrl)
            .then(resp => resp.blob())
            .then(async blob => {
                resolve(blob);
            })
            .catch((err) => {
                console.log(err);
                reject(false);
            });
    });
}


async function downloadFile(url) {
    const blob = await downloadFilePromise(url);
    if (blob) {
        try {
            const suggestedName = url.substring(url.lastIndexOf('/') + 1);
            // create a new handle
            const newHandle = await window.showSaveFilePicker({suggestedName: suggestedName});

            // create a FileSystemWritableFileStream to write to
            const writableStream = await newHandle.createWritable();

            // write our file
            await writableStream.write(blob);

            // close the file and write the contents to disk.
            await writableStream.close();

            return true;
        } catch (e) {
            console.log(e);
            return false;
        }
    }

    return false;
}


// Export excel file
async function export_file(type){
    if (type === "excel") {
        const excel_link = "https://pumbed.s3.eu-west-2.amazonaws.com/" + excel_file;
        await downloadFile(excel_link)
    }

    if (type === "pdf") {
        const csv_link = `https://pumbed.s3.eu-west-2.amazonaws.com/jobs/${job_id}/report.csv`;
        await downloadFile(csv_link);
        const pdf_link = csv_link.replace("report.csv", "pdfs.zip");
        await downloadFile(pdf_link);
    }

    if (type === "text") {
        const txts_link = `https://pumbed.s3.eu-west-2.amazonaws.com/jobs/${job_id}/txts.zip`;
        await downloadFile(txts_link);
    }
}

// show detail of row
function show_detail(id){

    var html = "";
    var ids = [
        "heading_title", "date", "abstract",
        "authors_list", "author_email", "affiliation",
        "pmcid", "doi", "mesh_terms",
        "publication_type"
    ];

    ids.forEach(function(ind, index){
        $('#' + ind).html(results[id][ind]);
    });

    $('#pubmed_link').html(results[id]['Pubmed link']);
    $('#pubmed_link').attr("href", results[id]['Pubmed link']);
    $('#author_email').attr("href", "mailto:" + results[id]['author_email']);

    $('#full_text_links').html(convert_full_text_links(results[id]['full_text_links']));

    $('#modal').modal('show');
}

// show detail of row
function show_clinical_detail(id){
    var html = "";
    var ids = [
        "nct_number", "conditions", "interventions", "outcome_measures",
        "heading_title", "date", "abstract",
        "authors_list", "author_email", "affiliation",
        "pmcid", "doi", "mesh_terms",
        "publication_type"
    ];

    ids.forEach(function(ind, index) {
        $('#' + ind).html(results[id][ind]);
    });

    $('#pubmed_link').html(results[id]['Pubmed link']);
    $('#pubmed_link').attr("href", results[id]['Pubmed link']);
    $('#author_email').attr("href", "mailto:" + results[id]['author_email']);

    $('#full_text_links').html(convert_full_text_links(results[id]['full_text_links']));

    $('#modal').modal('show');
}

//truncate long text
function truncate(str, len=100) {
    /*
        truncate text

        @params:
                n: string,
                len: int
        @return:
                truncated string
    */

    if(str.length <= len) {
        return str;
    }

    var ext = str.substring(str.length - 3, str.length);
    var filename = str.replace(ext,'');

    return filename.substr(0, len-3) + (str.length > len ? '\n ......' : '');
}


function reformat_text(text){
    return text.split("\n").join("<br/>");
}


function convert_full_text_links(full_text_links){
    /* convert full text links to links with a tag */
    var tags = full_text_links.split('\n');
    var html = "";
    for ( var i = 0 ; i < tags.length; i++ ){
        html += '<a href="' + tags[i].replace(',','') + '" target="_blank">' + tags[i] + '</a><br/>';
    }

    return html;
}


// Populate the table data
function populate_table(){
    var html = "";
    $('#table_div').empty();

    var table = '<table id="results_table" class="table table-striped table-bordered dt-responsive nowrap" style="width:100%"><thead><tr><th>_NO</th><th>Pubmed link</th><th>Title</th><th>Date</th><th>Abstract</th><th>Authors</th><th>Author email</th><th>Author affiliation</th><th>PMCID</th><th>DOI</th><th>Full text link</th><th>Mesh terms</th><th>Publication type</th></tr></thead><tbody></tbody>';
    $('#table_div').html(table);

    for ( var i = 0 ; i < results.length; i++ ){
        html += '<tr><td>' + (i+1) + "</td>";
        html +='<td><div class="width-100"><a href="' + results[i]["Pubmed link"] + '" target="_blank">' + results[i]["Pubmed link"] + "</a></div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-220">' + truncate(results[i]["heading_title"], 150) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-80">' + results[i]["date"] + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-250">' + reformat_text(truncate(results[i]["abstract"], 250)) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["authors_list"])) + "</div></td>";
        html +='<td><div class="width-100"><a href="mailto:' + results[i]["author_email"] + '">' + results[i]["author_email"] + "</a></div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-200">' + reformat_text(truncate(results[i]["affiliation"], 200)) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-80">' + results[i]["pmcid"] + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-100">' + results[i]["doi"] + "</div></td>";
        html +='<td><div class="width-220">' + convert_full_text_links(results[i]["full_text_links"]) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["mesh_terms"])) + "</div></td>";
        html +='<td onclick="show_detail(' + i + ')"><div class="width-100">' + reformat_text(results[i]["publication_types"]) + "</div></td>";
        html += "</tr>";
    }

    $('#results_table tbody').html(html);
    $('#results_table').DataTable({
        autoWidth: false, //step 1
        columnDefs: [
           { width: '300px', targets: 0 }, //step 2, column 1 out of 4
           { width: '300px', targets: 1 }, //step 2, column 2 out of 4
           { width: '300px', targets: 2 }  //step 2, column 3 out of 4
        ]
    });
}


// Populate the table data
function populate_clinical_table(){
    var html = "";
    $('#table_div').empty();

    var table = '<table id="results_table" class="table table-striped table-bordered dt-responsive nowrap" style="width:100%"><thead><tr><th>_NO</th><th>NCT number</th><th>Conditions</th><th>Interventions</th><th>Outcome measures</th><th>Pubmed link</th><th>Title</th><th>Date</th><th>Abstract</th><th>Authors</th><th>Author email</th><th>Author affiliation</th><th>PMCID</th><th>DOI</th><th>Full text link</th><th>Mesh terms</th><th>Publication type</th></tr></thead><tbody></tbody>';
    $('#table_clinical_div').html(table);

    for ( var i = 0 ; i < results.length; i++ ){
        html += '<tr><td>' + (i+1) + "</td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["nct_number"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["conditions"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["interventions"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["outcome_measures"], 150) + "</div></td>";
        html +='<td><div class="width-100"><a href="' + results[i]["Pubmed link"] + '" target="_blank">' + results[i]["Pubmed link"] + "</a></div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + truncate(results[i]["heading_title"], 150) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-80">' + results[i]["date"] + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-250">' + reformat_text(truncate(results[i]["abstract"], 250)) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["authors_list"])) + "</div></td>";
        html +='<td><div class="width-100"><a href="mailto:' + results[i]["author_email"] + '">' + results[i]["author_email"] + "</a></div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-200">' + reformat_text(truncate(results[i]["affiliation"], 200)) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-80">' + results[i]["pmcid"] + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + results[i]["doi"] + "</div></td>";
        html +='<td><div class="width-220">' + convert_full_text_links(results[i]["full_text_links"]) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-150">' + reformat_text(truncate(results[i]["mesh_terms"])) + "</div></td>";
        html +='<td onclick="show_clinical_detail(' + i + ')"><div class="width-100">' + reformat_text(results[i]["publication_types"]) + "</div></td>";
        html += "</tr>";
    }

    $('#results_table tbody').html(html);
    $('#results_table').DataTable({
        autoWidth: false, //step 1
        columnDefs: [
           { width: '300px', targets: 0 }, //step 2, column 1 out of 4
           { width: '300px', targets: 1 }, //step 2, column 2 out of 4
           { width: '300px', targets: 2 }  //step 2, column 3 out of 4
        ]
    });
}


// Create new job
async function create_job(data){
    show_spinner();
    let res = await AjaxRequest(hostName + '/api/create_job','POST', JSON.stringify(data));
    if (res.status === 200) {
        job_id = res.jobId;
        console.log(res);

        $('#pdf_download, #extract_texts').hide();
        pdf_downloaded = false;
        text_extracted = false;
        job_end = Date.now()/1000 + 300;
        recycle_function(check_job)
    } else {
        alert(res.message);
        hide_spinner();
    }
}


// checking restart
function recycle_function(func){
    if (Date.now()/1000 < job_end)
        setTimeout(() => {
            func();
        }, 10000);
    else {
        hide_spinner();
        alert("Job is not done by error.")
    }
}


// Check created job by job name
async function check_job(){
    try {
        let json_link = `https://pumbed.s3.eu-west-2.amazonaws.com/jobs/${job_id}/${job_id}.json`;
         let res = await AjaxRequest(json_link, 'GET', null, false);
         res = JSON.parse(res);

         switch (job_type) {
            case 'pubmed':
                get_results_pubmed(res);
                break;
            case 'clinical':
                get_results_clinical(res);
                break;
         }

    } catch (e) {
        recycle_function(check_job);
    }
}

function init_excel_files(){
    if (results.length === 0 || !excel_file) {
        setDownloadableState();
        alert('No Result!');
        return;
    }
    setDownloadableState('excel');
    alert("Scraping was finished, Please download Excel file in Downloadable list.");
    $('#pdf_download').show();
}

function get_results_pubmed(res) {
    /**
     *  Read JSON data from s3 bucket by job name of Pubmed Job,
     *  and showing results in pages.
     *  Making excel downloadable
     * */
    excel_file = res.excel_file;
    results = res.data;
    populate_table();
    init_excel_files();
}

// start scraping and show results in dataTable
$('#submit').click(async function(eve){
    job_type = "pubmed";
    var keyword = $('#query').val();
    if (keyword === ""){
        alert('Type search keyword please');
        return;
    }

    var data = {
        type: job_type,
        keyword: keyword
    };

    await create_job(data);
});


function get_results_clinical(res) {
    /**
     *  Read JSON data from s3 bucket by job name of Pubmed + Clinical Job,
     *  and showing results in pages.
     *  Making excel downloadable
     * */

    excel_file = res.excel_file;
    results = res.data;
    populate_clinical_table();
    init_excel_files();
}


$('#clinical_submit').click(async function(eve){
    var conditions_disease = $('#conditions_disease').val();
    var other_terms = $('#other_terms').val();
    if (conditions_disease === "" && other_terms === ""){
        alert('Type search keyword please');
        return;
    }
    job_type = "clinical";
    var data = {
        type: job_type,
        conditions_disease: conditions_disease,
        other_terms: other_terms
    };

    await create_job(data);
});


async function check_pdf_job() {
    let csv_link = `https://pumbed.s3.eu-west-2.amazonaws.com/jobs/${job_id}/report.csv`;
    try {
        pdf_downloaded = check_downloadable(csv_link);
        if (pdf_downloaded) {
            setDownloadableState("pdf");
            $('#extract_texts').show();
            alert("PDF downloading was finished, Please download PDF files in Downloadable list.");
        }
    } catch (e) {
        recycle_function(check_pdf_job);
    }
}


$('#pdf_download').click(async function(eve){
    show_spinner();
    if (!pdf_downloaded) {
        let data = {"job_id": job_id};
        const res = await AjaxRequest(hostName + '/api/create_pdf_job', 'POST', JSON.stringify(data));

        if (res.status === 200) {
            job_end = Date.now()/1000 + 300;
            recycle_function(check_pdf_job);
            text_extracted = false;
            $('#extract_texts').hide();
        } else {
            alert(res.message);
            hide_spinner();
        }
    } else {
        await check_pdf_job();
    }
});


function check_extract_job() {
    let txts_link = `https://pumbed.s3.eu-west-2.amazonaws.com/jobs/${job_id}/txts.zip`;

    try {
        text_extracted = check_downloadable(txts_link);
        if (text_extracted) {
            // todo: download csv, zip files here.
            // downloadFile(txts_link);
            setDownloadableState("text");
            alert("Text Extracting was finished, Please download Text files in Downloadable list.");
        }
    } catch (e) {
        recycle_function(check_extract_job);
    }
}


$('#extract_texts').click(async function(eve){
    show_spinner();
    if (!text_extracted) {
        if (pdf_downloaded) {
            let data = {"job_id": job_id, "action_type": "extract"};
            const res = await AjaxRequest(hostName + '/api/create_job', 'POST', JSON.stringify(data));
            console.log(res);
            if (res.status === 200){
                job_end = Date.now()/1000 + 300;
                recycle_function(check_extract_job);
            } else {
                alert(res.message);
                hide_spinner();
            }
        } else {
            alert("Please download pdf files first.")
        }
    } else {
        await check_extract_job();
    }
});


$(document).ready(function () {
    check_url();
    setDownloadableState();
});
