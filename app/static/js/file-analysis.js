/**
 * 文件分析功能扩展脚本
 * 提供文件上传、预览和深度AI分析功能
 */

// 文件分析相关的全局变量
let fileAnalysisQueue = [];
let isAnalyzing = false;

/**
 * 打开文件分析面板
 */
function openFileAnalysisPanel() {
    // 如果没有文件，先选择文件
    if (attachedFiles.length === 0) {
        fileInput.click();
        return;
    }
    
    // 触发深度分析
    analyzeAttachedFilesAI();
}

/**
 * 深度分析已上传的文件
 */
async function analyzeAttachedFilesAI() {
    if (attachedFiles.length === 0) {
        alert('请先上传文件');
        return;
    }
    
    if (isAnalyzing) {
        alert('正在分析中，请稍候...');
        return;
    }
    
    isAnalyzing = true;
    chatStatus.textContent = '🔍 深度分析中...';
    
    try {
        const formData = new FormData();
        
        // 添加所有附加的文件
        for (let fileObj of attachedFiles) {
            formData.append('files', fileObj.file);
        }
        
        // 显示分析开始提示
        addAssistantMessage('📊 正在分析您上传的文件，请稍候...');
        showTypingIndicator();
        
        const resp = await fetch('/api/analyze-files', {
            method: 'POST',
            body: formData
        });
        
        const data = await resp.json();
        hideTypingIndicator();
        
        if (resp.ok) {
            // 显示文件分析摘要
            let summary = '📁 **文件分析结果**\n\n';
            
            if (data.files && data.files.length > 0) {
                summary += '**上传文件：**\n';
                data.files.forEach((file, idx) => {
                    summary += `${idx + 1}. ${file.filename} (${file.format} - ${(file.size / 1024).toFixed(1)}KB)\n`;
                });
                summary += '\n';
            }
            
            if (data.errors && data.errors.length > 0) {
                summary += '**处理错误：**\n';
                data.errors.forEach(err => {
                    summary += `- ${err}\n`;
                });
                summary += '\n';
            }
            
            if (data.ai_analysis) {
                summary += '**AI 深度分析：**\n' + data.ai_analysis;
            }
            
            addAssistantMessage(summary);
            
            // 清空附加文件
            attachedFiles = [];
            filePreview.innerHTML = '';
            filePreview.classList.remove('has-files');
            
            if (chatStatus) {
                chatStatus.textContent = '✅ 分析完成';
                setTimeout(() => {
                    chatStatus.textContent = '随时为您解答各种问题';
                }, 2000);
            }
        } else {
            addAssistantMessage('❌ 分析失败: ' + (data.error || '未知错误'));
        }
    } catch (err) {
        console.error('Analysis error:', err);
        hideTypingIndicator();
        addAssistantMessage('❌ 分析过程出错: ' + err.message);
        chatStatus.textContent = '❌ 分析失败';
    } finally {
        isAnalyzing = false;
    }
}

/**
 * 快速分析单个文件
 */
async function quickAnalyzeFile(file) {
    const formData = new FormData();
    formData.append('files', file);
    
    try {
        const resp = await fetch('/api/upload-file', {
            method: 'POST',
            body: formData
        });
        
        const data = await resp.json();
        
        if (data.success_count > 0) {
            return data.files[0];
        } else {
            throw new Error(data.errors ? data.errors[0] : '分析失败');
        }
    } catch (err) {
        console.error('Quick analysis error:', err);
        throw err;
    }
}

/**
 * 显示文件分析详情面板
 */
function showFileAnalysisDetails(fileAnalysis) {
    let details = '📄 **文件详情**\n\n';
    details += `**文件名：** ${fileAnalysis.filename}\n`;
    details += `**类型：** ${fileAnalysis.type}\n`;
    details += `**格式：** ${fileAnalysis.format}\n`;
    details += `**大小：** ${(fileAnalysis.size / 1024).toFixed(1)}KB\n\n`;
    
    if (fileAnalysis.type === 'image') {
        if (fileAnalysis.dimensions) {
            details += `**尺寸：** ${fileAnalysis.dimensions[0]} × ${fileAnalysis.dimensions[1]} px\n`;
        }
        if (fileAnalysis.analysis && fileAnalysis.analysis.colors) {
            details += `**主要颜色：** ${fileAnalysis.analysis.colors.slice(0, 3).map(c => c.hex).join(', ')}\n`;
        }
    } else {
        if (fileAnalysis.analysis) {
            details += `**字符数：** ${fileAnalysis.analysis.char_count || 0}\n`;
            details += `**单词数：** ${fileAnalysis.analysis.word_count || 0}\n`;
            if (fileAnalysis.analysis.line_count) {
                details += `**行数：** ${fileAnalysis.analysis.line_count}\n`;
            }
            if (fileAnalysis.analysis.page_count) {
                details += `**页数：** ${fileAnalysis.analysis.page_count}\n`;
            }
        }
        if (fileAnalysis.text_preview) {
            details += `\n**内容预览：**\n\`\`\`\n${fileAnalysis.text_preview}\n\`\`\``;
        }
    }
    
    addAssistantMessage(details);
}

/**
 * 增强的文件选择处理
 */
function enhancedHandleFileSelect(files) {
    for (let file of files) {
        // 限制文件大小 10MB
        if (file.size > 10 * 1024 * 1024) {
            alert(`文件 ${file.name} 超过 10MB 限制`);
            continue;
        }
        
        const fileId = addFileToPreview(file);
        attachedFiles.push({ 
            id: fileId, 
            file: file,
            timestamp: Date.now()
        });
    }
    
    // 显示提示信息
    if (attachedFiles.length > 0) {
        const tipMessage = `📎 已选择 ${attachedFiles.length} 个文件，可点击"分析"按钮进行AI深度分析`;
        console.log(tipMessage);
    }
}

// 导出函数供其他脚本使用
window.fileAnalysis = {
    openPanel: openFileAnalysisPanel,
    analyzeFiles: analyzeAttachedFilesAI,
    quickAnalyze: quickAnalyzeFile,
    showDetails: showFileAnalysisDetails,
    handleFileSelect: enhancedHandleFileSelect
};

// 如果原脚本也定义了handleFileSelect，我们用增强版替换
if (typeof window.originalHandleFileSelect === 'undefined') {
    window.originalHandleFileSelect = handleFileSelect;
}
window.handleFileSelect = enhancedHandleFileSelect;
